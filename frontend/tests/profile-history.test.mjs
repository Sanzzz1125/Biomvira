import assert from 'node:assert/strict';
import { after, before, beforeEach, afterEach, test } from 'node:test';
import { JSDOM } from 'jsdom';
import { createServer } from 'vite';

// Establish the DOM before importing ReactDOM's event system.
const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: 'http://localhost' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const React = await import('react');
const { act } = React;
const { createRoot } = await import('react-dom/client');
let MemoryRouter;
let server, UserProfileForm, HistoryPage, LoginPage, Navbar, AuthProvider, ToastProvider, App, root;
let currentProfile, submissions;

before(async () => {
  server = await createServer({
    server: { middlewareMode: true, ws: false, hmr: false }, appType: 'custom',
    // Bundle React Router's ESM build so tests and app code share one router instance.
    ssr: { noExternal: ['react-router-dom', 'react-router'], resolve: { conditions: ['module-sync', 'module', 'node', 'development'] } },
  });
  ({ MemoryRouter } = await server.ssrLoadModule('/tests/router-shim.ts'));
  ({ UserProfileForm } = await server.ssrLoadModule('/src/components/UserProfileForm.tsx'));
  ({ HistoryPage } = await server.ssrLoadModule('/src/pages/HistoryPage.tsx'));
  ({ LoginPage } = await server.ssrLoadModule('/src/pages/auth/LoginPage.tsx'));
  ({ Navbar } = await server.ssrLoadModule('/src/components/Navbar.tsx'));
  ({ AuthProvider } = await server.ssrLoadModule('/src/auth/AuthContext.tsx'));
  ({ ToastProvider } = await server.ssrLoadModule('/src/components/Toast.tsx'));
  ({ App } = await server.ssrLoadModule('/src/App.tsx'));
});
after(async () => { await server?.close(); dom.window.close(); });
beforeEach(() => {
  root = createRoot(document.getElementById('root'));
  currentProfile = { age: 25, gender: 'female', diet_type: 'veg', allergens: [] };
  submissions = [];
});
afterEach(async () => { await act(() => root.unmount()); });

async function renderProfile() {
  function Harness() {
    const [profile, setProfile] = React.useState(currentProfile);
    currentProfile = profile;
    return React.createElement(UserProfileForm, {
      profile, setProfile, isLoading: false, onBack() {},
      onSubmit: (validated) => submissions.push(validated),
    });
  }
  await act(() => root.render(React.createElement(Harness)));
}
async function editAge(value) {
  const input = document.getElementById('age');
  await act(() => {
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(input, value);
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
  });
}
async function submit() {
  const button = [...document.querySelectorAll('button')].find(el => el.textContent.includes('Generate my plan'));
  await act(() => button.click());
}

test('age starts at 25 and stays empty after both digits are deleted', async () => {
  await renderProfile();
  assert.equal(document.getElementById('age').value, '25');
  await editAge('2');
  assert.equal(document.getElementById('age').value, '2');
  await editAge('');
  assert.equal(document.getElementById('age').value, '');
  // An unrelated profile update must not restore the old numeric age.
  const male = document.querySelector('[role="radio"][aria-checked="false"]');
  await act(() => male.click());
  assert.equal(document.getElementById('age').value, '');
  await submit();
  assert.equal(submissions.length, 0);
  assert.match(document.querySelector('[role="alert"]').textContent, /enter your age/i);
});

for (const age of [1, 18, 21, 30, 65, 120]) {
  test(`cleared age accepts and submits ${age} as a number`, async () => {
    await renderProfile();
    await editAge('');
    await editAge(String(age));
    await submit();
    assert.equal(submissions.length, 1);
    assert.equal(submissions[0].age, age);
    assert.equal(currentProfile.age, age);
    assert.equal(document.querySelector('[role="alert"]'), null);
  });
}
for (const invalid of ['0', '-1', '121', '18.5', 'abc']) {
  test(`invalid age ${invalid} is blocked`, async () => {
    await renderProfile();
    await editAge(invalid);
    await submit();
    assert.equal(submissions.length, 0);
    assert.ok(document.querySelector('[role="alert"]'));
    assert.equal(currentProfile.age, 25);
    assert.equal(document.getElementById('age').getAttribute('aria-invalid'), 'true');
  });
}

test('correcting an invalid age clears the error and submits the new value', async () => {
  await renderProfile();
  await editAge('');
  await submit();
  await editAge('21');
  assert.equal(document.querySelector('[role="alert"]'), null);
  await submit();
  assert.equal(submissions[0].age, 21);
});

const guest = { ok: true, status: 200, json: async () => ({ user: null }) };
const profileOf = (role) => ({
  id: 'u1', name: 'Asha Rao', email: 'asha@example.com', role, status: 'active', created_at: '2026-11-15T00:00:00Z',
});
const asUser = (role) => ({ ok: true, status: 200, json: async () => profileOf(role) });
const sessionOf = (role) => ({ ok: true, status: 200, json: async () => ({ user: profileOf(role) }) });

function withProviders(element, path = '/') {
  return React.createElement(MemoryRouter, { initialEntries: [path] },
    React.createElement(ToastProvider, null, React.createElement(AuthProvider, null, element)));
}
const settle = () => act(async () => { await new Promise(resolve => setTimeout(resolve, 0)); });

test('history asks guests to sign in and never requests saved reports', async () => {
  const originalFetch = globalThis.fetch;
  const requested = [];
  globalThis.fetch = async (url) => { requested.push(String(url)); return guest; };
  try {
    await act(() => root.render(withProviders(React.createElement(HistoryPage), '/history')));
    await settle();
    assert.match(document.body.textContent, /Sign in to see your saved reports/);
    assert.deepEqual(requested, ['/api/v1/auth/session']);
  } finally { globalThis.fetch = originalFetch; }
});

test('login validates input, then posts credentials as JSON', async () => {
  const originalFetch = globalThis.fetch;
  let loginBody;
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('/auth/login')) { loginBody = JSON.parse(options.body); return asUser('user'); }
    return guest;
  };
  try {
    await act(() => root.render(withProviders(React.createElement(LoginPage), '/login')));
    await settle();
    const form = document.querySelector('form');
    await act(() => form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true })));
    assert.match(document.body.textContent, /Enter your email address/);
    assert.equal(loginBody, undefined);
    const [email, password] = document.querySelectorAll('input');
    for (const [input, value] of [[email, ' asha@example.com '], [password, 'Nutri1ens!']]) {
      await act(() => {
        Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(input, value);
        input.dispatchEvent(new window.Event('input', { bubbles: true }));
      });
    }
    await act(async () => { form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true })); });
    await settle();
    assert.deepEqual(loginBody, { email: 'asha@example.com', password: 'Nutri1ens!' });
  } finally { globalThis.fetch = originalFetch; }
});

for (const [role, showsAdmin] of [['user', false], ['admin', true], ['owner', true]]) {
  test(`navigation ${showsAdmin ? 'shows' : 'hides'} the admin portal for a ${role}`, async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => sessionOf(role);
    try {
      await act(() => root.render(withProviders(React.createElement(Navbar, { onOpenDisclaimer() {} }))));
      await settle();
      const adminLinks = () => [...document.querySelectorAll('a')].filter(a => a.getAttribute('href') === '/admin');
      assert.equal(adminLinks().length, 0);  // no Admin button in the navbar for anyone
      const menu = [...document.querySelectorAll('button[aria-haspopup="menu"]')].find(b => !(b.getAttribute('aria-label') || '').startsWith('Language'));
      await act(async () => { menu.click(); });
      assert.equal(adminLinks().length > 0, showsAdmin);  // admins reach the portal from their account menu
      assert.equal([...document.querySelectorAll('a')].some(a => a.textContent === 'Log in'), false);
    } finally { globalThis.fetch = originalFetch; }
  });
}

test('the application defaults to 25 and sends an edited age through analysis to results', async () => {
  // Read the actual profile by moving through the existing workflow using DOM events.
  window.scrollTo = () => {};
  const originalFetch = globalThis.fetch;
  let submittedAnalysis;
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('/auth/session')) return guest;
    if (url.endsWith('/api/health')) return { ok: true, status: 200, json: async () => ({ status: 'online' }) };
    if (url.endsWith('/analyze-and-recommend')) {
      submittedAnalysis = JSON.parse(options.body);
      return { ok: true, json: async () => ({
        analysis_id: 'synthetic-analysis', timestamp: '2026-11-15T00:00:00Z',
        user_profile: submittedAnalysis.user_profile,
        status_summary: { low: 0, borderline: 0, normal: 0, high: 0 },
        marker_analyses: [], recommendations: [], grounded_explanation: 'Synthetic test result.',
        requires_physician_consult: false, consult_reasons: [],
      }) };
    }
    return { ok: true, json: async () => ({
    session_id: 'synthetic', sanitized_preview: '', warnings: [], unmatched_text_lines: [],
    extracted_biomarkers: [{ biomarker_key: 'vitamin_d', display_name: 'Vitamin D', detected_value: 12,
      detected_unit: 'ng/mL', canonical_value: 12, canonical_unit: 'ng/mL', report_reference_range: null,
      extraction_method: 'regex', confidence: null }],
  }) };
  };
  try {
    window.history.pushState({}, '', '/analyze');  // the analyser has its own page; the home page links to it
    await act(() => root.render(React.createElement(App)));
    // The analyser page loads on first visit (code splitting): wait for it like a user would.
    const findPaste = () => [...document.querySelectorAll('button')].find(el => el.textContent.includes('Paste text'));
    for (let i = 0; i < 100 && !findPaste(); i++) await act(() => new Promise(resolve => setTimeout(resolve, 20)));
    const pasteTab = findPaste();
    await act(() => pasteTab.click());
    const textarea = document.getElementById('report-text');
    await act(() => {
      Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')
        .set.call(textarea, '25-OH Vitamin D  12  ng/mL  30 - 100');
      textarea.dispatchEvent(new window.Event('input', { bubbles: true }));
    });
    const extract = [...document.querySelectorAll('button')].find(el => el.textContent.includes('Analyse my report'));
    await act(async () => { extract.click(); await new Promise(resolve => setTimeout(resolve, 1500)); });
    // A cleanly read report skips the review step and goes straight to the profile, with a summary to review from.
    assert.match(document.body.textContent, /1 result read from your report/);
    assert.equal(document.getElementById('age').value, '25');
    await editAge('');
    await editAge('65');
    await act(async () => {
      const generate = [...document.querySelectorAll('button')].find(el => el.textContent.includes('Generate my plan'));
      generate.click();
      await new Promise(resolve => setTimeout(resolve, 2600));
    });
    assert.equal(submittedAnalysis.user_profile.age, 65);
    assert.equal(submittedAnalysis.biomarkers[0].value, 12);
    assert.match(document.body.textContent, /Your personalised diet plan/);
    assert.match(document.body.textContent, /isn't saved because you're browsing as a guest/);
  } finally { globalThis.fetch = originalFetch; }
});
