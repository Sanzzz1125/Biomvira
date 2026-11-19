import assert from 'node:assert/strict';
import { after, afterEach, before, beforeEach, test } from 'node:test';
import { JSDOM } from 'jsdom';
import { createServer } from 'vite';

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: 'http://localhost' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.sessionStorage = dom.window.sessionStorage;
globalThis.localStorage = dom.window.localStorage;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const React = await import('react');
const { act } = React;
const { createRoot } = await import('react-dom/client');
let server, ChatAssistant, AuthProvider, MemoryRouter, setChatContext, root, requests;
const originalFetch = globalThis.fetch;
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const USER = { id: 'u1', name: 'Asha Rao', email: 'asha@example.com', role: 'user', status: 'active',
               created_at: '2026-11-01T00:00:00Z', last_login_at: null };

before(async () => {
  server = await createServer({
    server: { middlewareMode: true, ws: false, hmr: false }, appType: 'custom',
    ssr: { noExternal: ['react-router-dom', 'react-router'], resolve: { conditions: ['module-sync', 'module', 'node', 'development'] } },
  });
  ({ MemoryRouter } = await server.ssrLoadModule('/tests/router-shim.ts'));
  ({ ChatAssistant } = await server.ssrLoadModule('/src/components/ChatAssistant.tsx'));
  ({ AuthProvider } = await server.ssrLoadModule('/src/auth/AuthContext.tsx'));
  ({ setChatContext } = await server.ssrLoadModule('/src/lib/chatContext.ts'));
});
after(async () => { await server?.close(); dom.window.close(); });
beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  requests = [];
  root = createRoot(document.getElementById('root'));
});
afterEach(async () => {
  await act(() => root.unmount());
  await act(() => setChatContext(null));
  globalThis.fetch = originalFetch;
});

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
const reply = (over = {}) => ({ reply: 'Hello', kind: 'answer', suggestions: [], topic: null, conversation_id: null, saved: false, ...over });

/** Routes fetch calls like the real API. `chatReplies` is consumed in order for POST /chat. */
function mockApi({ user = null, chatReplies = [], conversations = [], details = {}, failChat = false } = {}) {
  globalThis.fetch = async (url, options = {}) => {
    const path = String(url).replace(/^https?:\/\/[^/]+/, '');
    const method = (options.method || 'GET').toUpperCase();
    requests.push({ path, method, body: options.body ? JSON.parse(options.body) : null });
    if (path.endsWith('/auth/session')) return json({ user });
    if (path.endsWith('/chat') && method === 'POST') {
      if (failChat) return json({ detail: 'boom' }, 500);
      return json(chatReplies.shift() ?? reply());
    }
    if (path.endsWith('/chat/conversations')) return json(conversations);
    const detail = path.match(/\/chat\/conversations\/([^/]+)$/);
    if (detail && method === 'DELETE') return new Response(null, { status: 204 });
    if (detail) return details[detail[1]] ? json(details[detail[1]]) : json({ detail: 'Chat not found.' }, 404);
    return json({ detail: 'not found' }, 404);
  };
}

async function render() {
  await act(async () => {
    root.render(
      React.createElement(MemoryRouter, null,
        React.createElement(AuthProvider, null, React.createElement(ChatAssistant)))
    );
    await wait(30);
  });
}

const button = (label) =>
  [...document.querySelectorAll('button, a')].find((b) => b.textContent.trim() === label || b.getAttribute('aria-label') === label
    || b.textContent.includes(label));
const chatPosts = () => requests.filter((r) => r.path.endsWith('/chat') && r.method === 'POST').map((r) => r.body);

async function openPanel() {
  await act(async () => { button('Ask NutriLens').click(); await wait(60); });
}

async function ask(text, ms = 650) {
  const box = document.getElementById('nl-assistant-input');
  await act(() => {
    Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set.call(box, text);
    box.dispatchEvent(new window.Event('input', { bubbles: true }));
  });
  await act(async () => {
    box.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    await wait(ms);
  });
}

test('guests see the welcome view, get formatted answers and follow-ups keep the topic', async () => {
  mockApi({ chatReplies: [
    reply({ reply: '**Foods that help with low Hemoglobin**\n\nGood vegetarian choices:\n- **Garden Cress Seeds / Halim**: 10 mg iron per 100 g\n- **Little Millet (Kutki)**: 9.3 mg iron per 100 g\n\n**Tips:**\n- Add lemon to iron-rich meals.',
            topic: 'test:hemoglobin', suggestions: ['What is the normal range of Hemoglobin?'] }),
    reply({ reply: 'Adults: 12 to 15.5 g/dL', topic: 'test:hemoglobin' }),
  ] });
  await render();
  await openPanel();
  assert.ok(document.querySelector('[role="dialog"]'));
  assert.match(document.body.textContent, /How can I help\?/);
  assert.ok(button('What does high TSH mean?'), 'starter cards are shown');
  assert.equal(button('Past chats'), undefined, 'guests have no saved chats');
  assert.match(document.body.textContent, /Chats aren't saved/);

  await ask('foods for low hb');
  const log = document.querySelector('[role="log"]');
  assert.equal(log.querySelector('h3').textContent, 'Foods that help with low Hemoglobin');
  const rows = [...log.querySelectorAll('ul li')].map((li) => li.textContent);
  assert.ok(rows.some((r) => r.includes('Garden Cress Seeds / Halim') && r.includes('10 mg iron')), rows.join('|'));
  assert.ok(rows.some((r) => r.includes('Little Millet') && r.includes('Kutki')), 'Hindi name shown as a sub-label');
  assert.match(log.textContent, /Tips/);
  assert.ok(button('What is the normal range of Hemoglobin?'), 'follow-up suggestions are shown');
  assert.deepEqual(chatPosts()[0], { message: 'foods for low hb', topic: null, context: null, conversation_id: null, report_id: null, language: 'en', history: [] });

  await act(async () => { button('What is the normal range of Hemoglobin?').click(); await wait(650); });
  assert.equal(chatPosts()[1].topic, 'test:hemoglobin');
  assert.match(sessionStorage.getItem('nl_assistant_v2'), /foods for low hb/);
});

test('safety replies show call buttons', async () => {
  mockApi({ chatReplies: [reply({ kind: 'safety', reply: 'This could be an emergency. **Please call 112 or 108.**' })] });
  await render();
  await openPanel();
  await ask('i have chest pain');
  assert.match(document.body.textContent, /Get help now/);
  assert.equal(document.querySelector('a[href="tel:108"]').textContent, 'Call 108');
});

test('a failed message offers Retry and resends without duplicating the question', async () => {
  mockApi({ failChat: true });
  await render();
  await openPanel();
  await ask('what is tsh');
  assert.match(document.body.textContent, /Couldn't reach NutriLens/);
  mockApi({ chatReplies: [reply({ reply: 'TSH is a thyroid hormone.' })] });
  await act(async () => { button('Retry').click(); await wait(650); });
  assert.match(document.body.textContent, /TSH is a thyroid hormone/);
  assert.equal([...document.querySelectorAll('[role="log"] .bg-brand-600')].filter((b) => b.textContent === 'what is tsh').length, 1);
});

test('signed-in users continue their saved chat, see past chats, and start new ones', async () => {
  mockApi({
    user: USER,
    conversations: [
      { id: 'c1', title: 'What is tsh', report_id: null, report_date: null, preview: 'TSH is…', message_count: 2, updated_at: '2026-11-16T12:40:00Z' },
      { id: 'c2', title: 'Is my HbA1c ok?', report_id: 'r9', report_date: '2026-08-02T10:00:00Z', preview: 'Your HbA1c…', message_count: 2, updated_at: '2026-08-02T10:00:00Z' },
    ],
    details: { c1: { id: 'c1', title: 'What is tsh', report_id: null, report_date: null, topic: 'test:tsh', updated_at: '2026-11-16T12:40:00Z',
                     messages: [{ role: 'user', text: 'what is tsh', kind: 'user', suggestions: [], created_at: '2026-11-16T12:40:00Z' },
                                { role: 'bot', text: 'TSH is a thyroid hormone.', kind: 'answer', suggestions: [], created_at: '2026-11-16T12:40:00Z' }] } },
    chatReplies: [reply({ reply: 'Adults: 0.4 to 4', conversation_id: 'c1', saved: true, topic: 'test:tsh' })],
  });
  await render();
  await openPanel();
  await act(() => wait(100));
  assert.match(document.body.textContent, /Continued from/);
  assert.match(document.body.textContent, /TSH is a thyroid hormone/);
  await ask('and the normal range?');
  assert.equal(chatPosts()[0].conversation_id, 'c1');
  assert.equal(chatPosts()[0].topic, 'test:tsh');

  await act(async () => { button('Past chats').click(); await wait(60); });
  assert.match(document.body.textContent, /Your chats/);
  assert.match(document.body.textContent, /General questions/);
  assert.match(document.body.textContent, /Other reports/);
  assert.match(document.body.textContent, /Open now/);

  await act(async () => { button('New chat').click(); await wait(30); });
  assert.match(document.body.textContent, /How can I help, Asha\?/);
  assert.match(document.body.textContent, /your chats are saved to your account/);
  mockApi({ user: USER, chatReplies: [reply({ conversation_id: 'c3', saved: true })] });
  await ask('is nutrilens free');
  assert.equal(chatPosts().at(-1).conversation_id, null, 'a new chat starts a new conversation');
  assert.equal(chatPosts().at(-1).message, 'is nutrilens free');
});

test('on a saved report the chat is linked to that report', async () => {
  mockApi({ user: USER, chatReplies: [reply({ conversation_id: 'c5', saved: true })] });
  await act(() => setChatContext({ markers: [{ key: 'hemoglobin', name: 'Hemoglobin', value: 10.4, unit: 'g/dL', status: 'low', range_low: 12, range_high: 15.5 }],
                                    plans: [], diet_type: 'veg', allergens: [], reportId: 'r1', reportDate: '2026-11-16T12:00:00Z', needAttention: 1 }));
  await render();
  assert.match(document.body.textContent, /Questions about your results\?/, 'a one-time hint appears on the results page');
  await openPanel();
  assert.match(document.body.textContent, /Report of/);
  assert.match(document.body.textContent, /chat saved with this report/);
  await act(async () => { button('Summarise my results').click(); await wait(650); });
  const body = chatPosts()[0];
  assert.equal(body.report_id, 'r1');
  assert.equal(body.context.markers[0].value, 10.4);
});

test('empty messages are ignored and Escape closes the panel', async () => {
  mockApi();
  await render();
  await openPanel();
  await ask('   ', 50);
  assert.equal(chatPosts().length, 0);
  assert.ok(button('Send message').disabled);
  await act(() => document.querySelector('[role="dialog"]').dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true })));
  assert.equal(document.querySelector('[role="dialog"]'), null);
});
