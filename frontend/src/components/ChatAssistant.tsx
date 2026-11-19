import { currentLanguage } from '../lib/i18n';
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Apple,
  ArrowUp,
  BookOpen,
  Check,
  ChevronLeft,
  CircleAlert,
  Copy,
  FileText,
  History,
  Lock,
  MessageCircleQuestion,
  Plus,
  ShieldAlert,
  ShieldCheck,
  SquarePen,
  Stethoscope,
  Trash2,
  X,
} from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { askAssistant, AssistantReply, chatApi, ChatDetail, ChatSummary } from '../services/api';
import { ApiError } from '../services/http';
import { contextPayload, useChatContext } from '../lib/chatContext';
import { plainText, RichAnswer } from './assistant/RichAnswer';
import { cx } from './ui';

type Kind = AssistantReply['kind'] | 'error' | 'user';

interface Message {
  id: number;
  role: 'user' | 'bot';
  text: string;
  kind?: Kind;
  suggestions?: string[];
  at: string;
  /** For an error: the question to send again. */
  retry?: string;
  /** For an error: the chat is full and needs a new one. */
  full?: boolean;
}

interface Conversation {
  id: string | null;
  reportId: string | null;
  topic: string | null;
  messages: Message[];
  resumedAt: string | null;
}

const GUEST_KEY = 'nl_assistant_v2';
const HINT_KEY = 'nl_assistant_hint_seen';
const MAX_LENGTH = 500;
const emptyConversation = (reportId: string | null = null): Conversation => ({
  id: null,
  reportId,
  topic: null,
  messages: [],
  resumedAt: null,
});

const GENERAL_STARTERS = [
  { icon: Activity, title: 'Understand a result', ask: 'What does high TSH mean?' },
  { icon: Apple, title: 'Find foods', ask: 'Iron foods for vegetarians' },
  { icon: BookOpen, title: 'Use NutriLens', ask: 'How do I get my diet plan?' },
  { icon: ShieldCheck, title: 'Privacy & safety', ask: 'Is my report stored?' },
];
const RESULT_STARTERS = [
  { icon: Activity, title: 'Your results', ask: 'Summarise my results' },
  { icon: Apple, title: 'Your food plan', ask: 'What should I eat?' },
  { icon: Stethoscope, title: 'Doctor review', ask: 'When should I see a doctor?' },
  { icon: ShieldCheck, title: 'Privacy & safety', ask: 'Is my report stored?' },
];

let messageSeq = 1;
const nextId = () => messageSeq++;

function readStorage<T>(key: string, fallback: T): T {
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeStorage(key: string, value: unknown) {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage can be unavailable (private mode); the chat still works */
  }
}

function loadGuestConversation(): Conversation {
  const saved = readStorage<Conversation | null>(GUEST_KEY, null);
  if (!saved || !Array.isArray(saved.messages)) return emptyConversation();
  saved.messages.forEach((m) => (messageSeq = Math.max(messageSeq, m.id + 1)));
  return { ...emptyConversation(), topic: saved.topic ?? null, messages: saved.messages };
}

function fromDetail(detail: ChatDetail): Conversation {
  return {
    id: detail.id,
    reportId: detail.report_id,
    topic: detail.topic,
    resumedAt: detail.updated_at,
    messages: detail.messages.map((m) => ({
      id: nextId(),
      role: m.role,
      text: m.text,
      kind: m.role === 'bot' ? (m.kind as Kind) : 'user',
      suggestions: m.suggestions,
      at: m.created_at,
    })),
  };
}

const time = (iso: string) => {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' });
};
const day = (iso: string | null) => {
  const date = iso ? new Date(iso) : null;
  return date && !Number.isNaN(date.getTime())
    ? date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    : '';
};
const shortDay = (iso: string) => {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

const iconButton =
  'flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 max-sm:h-11 max-sm:w-11';

const BotAvatar: React.FC<{ size?: 'sm' | 'lg' }> = ({ size = 'sm' }) => (
  <span
    className={cx(
      'flex shrink-0 items-center justify-center border border-brand-100 bg-brand-50 text-brand-600',
      size === 'sm' ? 'h-7 w-7 rounded-[9px]' : 'h-[52px] w-[52px] rounded-2xl'
    )}
  >
    <MessageCircleQuestion className={size === 'sm' ? 'h-3.5 w-3.5' : 'h-6 w-6'} aria-hidden />
  </span>
);

const SafetyCard: React.FC<{ text: string }> = ({ text }) => {
  const numbers = text.includes('14416') ? ['14416', '112'] : ['108', '112'];
  return (
    <article role="alert" className="ml-[38px] space-y-2.5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3.5">
      <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-red-700">
        <ShieldAlert className="h-4 w-4" aria-hidden />
        Get help now
      </p>
      <div className="text-sm leading-relaxed text-red-900">
        <RichAnswer text={text} />
      </div>
      <div className="flex gap-2">
        {numbers.map((n, i) => (
          <a
            key={n}
            href={`tel:${n}`}
            className={cx(
              'flex h-10 flex-1 items-center justify-center rounded-[10px] text-sm font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500',
              i === 0 ? 'bg-red-700 text-white hover:bg-red-800' : 'border border-red-200 bg-white text-red-700 hover:bg-red-50'
            )}
          >
            Call {n}
          </a>
        ))}
      </div>
    </article>
  );
};

export const ChatAssistant: React.FC = () => {
  const { user } = useAuth();
  const context = useChatContext();
  const signedIn = Boolean(user);
  const scopeReportId = signedIn ? context?.reportId ?? null : null;
  const scopeKey = user ? `${user.id}:${scopeReportId ?? 'general'}` : 'guest';

  const [open, setOpen] = useState(false);
  const [view, setView] = useState<'chat' | 'history'>('chat');
  const [conv, setConv] = useState<Conversation>(() => (signedIn ? emptyConversation() : loadGuestConversation()));
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [chats, setChats] = useState<ChatSummary[] | null>(null);
  const [chatsError, setChatsError] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [copied, setCopied] = useState<number | null>(null);
  const [hintSeen, setHintSeen] = useState(() => readStorage(HINT_KEY, false));

  const convRef = useRef(conv);
  convRef.current = conv;
  const loadedScope = useRef<string | null>(null);
  const loadToken = useRef(0);
  const firstScope = useRef(true);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const launcherRef = useRef<HTMLButtonElement>(null);

  // A different person or a different report means a different conversation.
  useEffect(() => {
    if (firstScope.current) {
      firstScope.current = false;
      return;
    }
    loadToken.current += 1;
    loadedScope.current = null;
    setLoadingChat(false);
    setView('chat');
    setChats(null);
    setConv(scopeKey === 'guest' ? loadGuestConversation() : emptyConversation(scopeReportId));
  }, [scopeKey, scopeReportId]);

  // Signed in: when the panel opens, continue the latest saved chat for this report (or the latest general chat).
  useEffect(() => {
    if (!open || !signedIn || loadedScope.current === scopeKey) return;
    loadedScope.current = scopeKey;
    const token = ++loadToken.current;
    setLoadingChat(true);
    (async () => {
      try {
        const list = await chatApi.list();
        if (token !== loadToken.current) return;
        setChats(list);
        const latest = list.find((c) => (c.report_id ?? null) === scopeReportId);
        if (latest && convRef.current.messages.length === 0) {
          const detail = await chatApi.get(latest.id);
          if (token === loadToken.current && convRef.current.messages.length === 0) setConv(fromDetail(detail));
        }
      } catch {
        /* the chat still works; it just starts fresh */
      } finally {
        if (token === loadToken.current) setLoadingChat(false);
      }
    })();
  }, [open, signedIn, scopeKey, scopeReportId]);

  useEffect(() => {
    if (!signedIn) writeStorage(GUEST_KEY, { topic: conv.topic, messages: conv.messages.slice(-40) });
  }, [conv, signedIn]);

  useLayoutEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [conv.messages, busy, open, view, loadingChat]);

  useEffect(() => {
    if (open && view === 'chat') inputRef.current?.focus();
  }, [open, view]);

  // On phones the panel covers the screen, so stop the page behind it from scrolling.
  useEffect(() => {
    if (!open || !window.matchMedia?.('(max-width: 639px)')?.matches) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  useLayoutEffect(() => {
    const box = inputRef.current;
    if (!box) return;
    box.style.height = 'auto';
    box.style.height = `${Math.min(box.scrollHeight, 112)}px`;
  }, [input, open, view]);

  const openPanel = () => {
    setOpen(true);
    if (!hintSeen) {
      setHintSeen(true);
      writeStorage(HINT_KEY, true);
    }
  };

  const close = useCallback(() => {
    setOpen(false);
    setTimeout(() => launcherRef.current?.focus(), 0);
  }, []);

  const appendBot = (message: Omit<Message, 'id' | 'role' | 'at'>) =>
    setConv((c) => ({
      ...c,
      messages: [...c.messages, { id: nextId(), role: 'bot', at: new Date().toISOString(), ...message }],
    }));

  const send = async (raw: string, options: { resend?: number } = {}) => {
    const text = raw.trim().slice(0, MAX_LENGTH);
    if (!text || busy) return;
    if (options.resend !== undefined) {
      setConv((c) => ({ ...c, messages: c.messages.filter((m) => m.id !== options.resend) }));
    } else {
      setConv((c) => ({
        ...c,
        messages: [...c.messages, { id: nextId(), role: 'user', text, kind: 'user', at: new Date().toISOString() }],
      }));
      setInput('');
    }
    setBusy(true);
    const started = Date.now();
    const ask = (conversationId: string | null) => {
      const current = convRef.current;
      // A chat from another report must not borrow this page's results.
      const pageMatches = !current.reportId || current.reportId === context?.reportId;
      return askAssistant({
        message: text,
        topic: current.topic,
        context: pageMatches ? contextPayload(context) : null,
        conversation_id: signedIn ? conversationId : null,
        report_id: signedIn && !conversationId ? current.reportId : null,
        language: currentLanguage(),
        history: signedIn ? [] : current.messages
          .filter((m, i, all) => !(i === all.length - 1 && m.role === 'user' && m.text === text))
          .slice(-6).map((m) => ({ role: m.role, text: m.text.slice(0, 4000) })),
      });
    };
    try {
      let reply: AssistantReply;
      try {
        reply = await ask(convRef.current.id);
      } catch (error) {
        // The saved chat was deleted elsewhere: carry on in a new one.
        if (error instanceof ApiError && error.status === 404 && convRef.current.id) {
          convRef.current = { ...convRef.current, id: null };
          setConv((c) => ({ ...c, id: null }));
          reply = await ask(null);
        } else {
          throw error;
        }
      }
      await new Promise((resolve) => setTimeout(resolve, Math.max(0, 400 - (Date.now() - started))));
      setConv((c) => ({
        ...c,
        id: reply.conversation_id ?? c.id,
        topic: reply.topic ?? (reply.kind === 'refuse' ? null : c.topic),
        messages: [
          ...c.messages,
          {
            id: nextId(),
            role: 'bot',
            text: reply.reply,
            kind: reply.kind,
            suggestions: reply.suggestions,
            at: new Date().toISOString(),
          },
        ],
      }));
      if (reply.saved) setChats(null);
    } catch (error) {
      const status = error instanceof ApiError ? error.status : 0;
      if (status === 409) {
        appendBot({ kind: 'error', text: 'This chat is full. Start a new chat to keep going.', full: true });
      } else {
        appendBot({
          kind: 'error',
          text:
            status === 429
              ? 'You are sending messages very quickly. Please wait a moment.'
              : "Couldn't reach NutriLens. Please check your connection.",
          retry: text,
        });
      }
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  };

  const newChat = () => {
    loadToken.current += 1;
    loadedScope.current = scopeKey;
    setLoadingChat(false);
    setConv(emptyConversation(scopeReportId));
    setView('chat');
    setInput('');
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const showHistory = async () => {
    setView('history');
    setChatsError(false);
    setConfirmDelete(null);
    try {
      setChats(await chatApi.list());
    } catch {
      setChatsError(true);
    }
  };

  const openChat = async (summary: ChatSummary) => {
    const token = ++loadToken.current;
    loadedScope.current = scopeKey;
    setView('chat');
    setLoadingChat(true);
    try {
      const detail = await chatApi.get(summary.id);
      if (token === loadToken.current) setConv(fromDetail(detail));
    } catch {
      if (token === loadToken.current) {
        setConv(emptyConversation(scopeReportId));
        appendBot({ kind: 'error', text: "Couldn't open that chat. It may have been deleted." });
      }
    } finally {
      if (token === loadToken.current) setLoadingChat(false);
    }
  };

  const deleteChat = async (summary: ChatSummary) => {
    if (confirmDelete !== summary.id) {
      setConfirmDelete(summary.id);
      return;
    }
    setConfirmDelete(null);
    try {
      await chatApi.remove(summary.id);
      setChats((list) => (list ?? []).filter((c) => c.id !== summary.id));
      if (convRef.current.id === summary.id) setConv(emptyConversation(scopeReportId));
    } catch {
      setChatsError(true);
    }
  };

  const copy = async (message: Message) => {
    try {
      await navigator.clipboard?.writeText(plainText(message.text));
      setCopied(message.id);
      setTimeout(() => setCopied((id) => (id === message.id ? null : id)), 1500);
    } catch {
      /* clipboard can be blocked; nothing to do */
    }
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void send(input);
    }
  };

  const firstName = user?.name?.trim().split(/\s+/)[0];
  const starters = context ? RESULT_STARTERS : GENERAL_STARTERS;
  const lastBot = [...conv.messages].reverse().find((m) => m.role === 'bot');
  const linkedToPage = Boolean(context && (!conv.reportId || conv.reportId === context.reportId));
  const showHint = Boolean(context) && !open && !hintSeen;

  const list = chats ?? [];
  const groups = [
    {
      label: scopeReportId ? `This report · ${day(context?.reportDate ?? null)}` : '',
      items: scopeReportId ? list.filter((c) => c.report_id === scopeReportId) : [],
    },
    { label: 'Other reports', items: list.filter((c) => c.report_id && c.report_id !== scopeReportId) },
    { label: 'General questions', items: list.filter((c) => !c.report_id) },
  ].filter((g) => g.items.length > 0);

  return (
    <>
      {showHint && (
        <div className="fixed bottom-[88px] right-5 z-40 hidden w-[300px] sm:flex max-w-[calc(100vw-2.5rem)] animate-fade-up items-start gap-3 rounded-2xl border border-slate-200 bg-white p-3.5 pl-4 shadow-card-lg">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] bg-brand-50 text-brand-600">
            <MessageCircleQuestion className="h-4 w-4" aria-hidden />
          </span>
          <button type="button" onClick={openPanel} className="min-w-0 flex-1 text-left focus:outline-none">
            <span className="block text-sm font-semibold text-slate-900">Questions about your results?</span>
            <span className="mt-0.5 block text-[13px] leading-relaxed text-slate-600">
              Ask me what any value means or which foods help.
            </span>
          </button>
          <button
            type="button"
            aria-label="Dismiss"
            onClick={() => {
              setHintSeen(true);
              writeStorage(HINT_KEY, true);
            }}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            <X className="h-3.5 w-3.5" aria-hidden />
          </button>
        </div>
      )}

      <button
        ref={launcherRef}
        type="button"
        onClick={() => (open ? close() : openPanel())}
        aria-expanded={open}
        aria-controls="nl-assistant"
        className={cx(
          'fixed bottom-5 right-5 z-40 flex h-[52px] items-center gap-2.5 rounded-full bg-brand-600 pl-2 pr-5 text-[14.5px] font-semibold text-white shadow-[0_10px_24px_-6px_rgba(22,124,100,0.45),0_2px_6px_rgba(15,23,42,0.08)] transition hover:bg-brand-700 focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-300',
          open && 'max-sm:hidden'
        )}
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/15">
          {open ? (
            <X className="h-[18px] w-[18px]" aria-hidden />
          ) : (
            <MessageCircleQuestion className="h-[18px] w-[18px]" aria-hidden />
          )}
        </span>
        {open ? 'Close' : 'Ask NutriLens'}
      </button>

      {open && (
        <section
          id="nl-assistant"
          role="dialog"
          aria-label="NutriLens assistant"
          onKeyDown={(e) => e.key === 'Escape' && close()}
          className="fixed inset-0 z-50 flex animate-fade-up flex-col bg-white sm:inset-auto sm:bottom-24 sm:right-5 sm:h-[min(720px,calc(100vh-7.5rem))] sm:w-[440px] sm:overflow-hidden sm:rounded-[20px] sm:border sm:border-slate-200 sm:shadow-[0_24px_48px_-12px_rgba(15,23,42,0.18),0_4px_10px_rgba(15,23,42,0.05)]"
        >
          {view === 'history' ? (
            <>
              <header className="flex items-center gap-2 border-b border-slate-100 py-3 pl-2.5 pr-3.5">
                <button type="button" aria-label="Back to chat" onClick={() => setView('chat')} className={iconButton}>
                  <ChevronLeft className="h-[18px] w-[18px]" aria-hidden />
                </button>
                <h2 className="flex-1 text-[15px] font-semibold text-slate-900">Your chats</h2>
                <button type="button" aria-label="Close assistant" onClick={close} className={iconButton}>
                  <X className="h-[18px] w-[18px]" aria-hidden />
                </button>
              </header>
              <div className="flex-1 space-y-[18px] overflow-y-auto p-3.5">
                <button
                  type="button"
                  onClick={newChat}
                  className="flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-brand-600 text-sm font-semibold text-white transition hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
                >
                  <Plus className="h-4 w-4" aria-hidden />
                  {scopeReportId ? 'New chat about this report' : 'New chat'}
                </button>
                {chatsError && (
                  <p className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-[13px] text-amber-900">
                    <CircleAlert className="h-4 w-4 shrink-0" aria-hidden />
                    Couldn't load your chats.
                    <button
                      type="button"
                      onClick={showHistory}
                      className="ml-auto font-semibold underline-offset-2 hover:underline"
                    >
                      Retry
                    </button>
                  </p>
                )}
                {!chats && !chatsError && (
                  <div className="space-y-2" aria-label="Loading chats">
                    {[0, 1, 2].map((i) => (
                      <div key={i} className="h-[60px] animate-pulse rounded-xl bg-slate-100" />
                    ))}
                  </div>
                )}
                {chats && groups.length === 0 && (
                  <p className="px-1 py-6 text-center text-sm text-slate-500">No saved chats yet.</p>
                )}
                {groups.map((group) => (
                  <div key={group.label} className="space-y-1.5">
                    <p className="px-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500">
                      {group.label}
                    </p>
                    {group.items.map((chat) => {
                      const active = chat.id === conv.id;
                      const confirming = confirmDelete === chat.id;
                      return (
                        <div
                          key={chat.id}
                          className={cx(
                            'flex items-center gap-1 rounded-xl border pr-1.5',
                            active ? 'border-brand-200 bg-brand-50' : 'border-transparent hover:bg-slate-50'
                          )}
                        >
                          <button
                            type="button"
                            onClick={() => openChat(chat)}
                            className="flex min-w-0 flex-1 flex-col gap-0.5 rounded-xl px-3 py-2.5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                          >
                            <span className="flex items-baseline justify-between gap-2">
                              <span className="truncate text-[13.5px] font-semibold text-slate-900">{chat.title}</span>
                              <span
                                className={cx('shrink-0 text-xs', active ? 'font-medium text-brand-700' : 'text-slate-500')}
                              >
                                {active ? 'Open now' : shortDay(chat.updated_at)}
                              </span>
                            </span>
                            <span className="truncate text-[12.5px] text-slate-600">
                              {group.label === 'Other reports' && chat.report_date
                                ? `Report of ${day(chat.report_date)}`
                                : chat.preview || 'No answer yet'}
                            </span>
                          </button>
                          <button
                            type="button"
                            onClick={() => deleteChat(chat)}
                            aria-label={confirming ? `Confirm delete ${chat.title}` : `Delete ${chat.title}`}
                            className={cx(
                              'flex h-8 shrink-0 items-center justify-center rounded-lg text-xs font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                              confirming
                                ? 'bg-red-600 px-2.5 text-white hover:bg-red-700'
                                : 'w-8 text-slate-500 hover:bg-slate-100 hover:text-red-600'
                            )}
                          >
                            {confirming ? 'Delete' : <Trash2 className="h-4 w-4" aria-hidden />}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
              <p className="border-t border-slate-100 px-4 pb-4 pt-3 text-center text-xs leading-relaxed text-slate-500">
                Chats are saved to your account. Deleting a report also deletes its chats.
              </p>
            </>
          ) : (
            <>
              <header className="flex items-center gap-3 border-b border-slate-100 py-3 pl-[18px] pr-3 max-sm:pl-1.5">
                <button type="button" aria-label="Close assistant" onClick={close} className={cx(iconButton, 'sm:hidden')}>
                  <ChevronLeft className="h-5 w-5" aria-hidden />
                </button>
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white">
                  <MessageCircleQuestion className="h-[18px] w-[18px]" aria-hidden />
                </span>
                <div className="min-w-0 flex-1">
                  <h2 className="text-[15px] font-semibold leading-tight text-slate-900">NutriLens Assistant</h2>
                  <p className="mt-0.5 flex items-center gap-1.5 truncate text-xs text-slate-500">
                    <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" aria-hidden />
                    {linkedToPage ? 'Using the results on this page' : 'Tests, foods and using NutriLens'}
                  </p>
                </div>
                {conv.messages.length > 0 && (
                  <button type="button" aria-label="New chat" title="New chat" onClick={newChat} className={iconButton}>
                    <SquarePen className="h-[18px] w-[18px]" aria-hidden />
                  </button>
                )}
                {signedIn && (
                  <button type="button" aria-label="Past chats" title="Past chats" onClick={showHistory} className={iconButton}>
                    <History className="h-[18px] w-[18px]" aria-hidden />
                  </button>
                )}
                <button
                  type="button"
                  aria-label="Close assistant"
                  onClick={close}
                  className={cx(iconButton, 'max-sm:hidden')}
                >
                  <X className="h-[18px] w-[18px]" aria-hidden />
                </button>
              </header>

              {context && linkedToPage && (
                <div className="mx-3.5 mt-3 flex items-center gap-2.5 rounded-xl border border-brand-100 bg-brand-50 px-3 py-2.5">
                  <FileText className="h-4 w-4 shrink-0 text-brand-700" aria-hidden />
                  <div className="min-w-0">
                    <p className="text-[13px] font-semibold text-brand-800">
                      {context.reportId ? `Report of ${day(context.reportDate)}` : 'Results on this page'}
                    </p>
                    <p className="truncate text-xs text-brand-700">
                      {context.markers.length} results · {context.needAttention} need attention
                      {context.reportId && signedIn ? ' · chat saved with this report' : ''}
                    </p>
                  </div>
                </div>
              )}

              <div
                ref={listRef}
                role="log"
                aria-live="polite"
                aria-busy={busy || loadingChat}
                className={cx(
                  'flex-1 space-y-3.5 overflow-y-auto bg-slate-50 px-4 py-4',
                  context && linkedToPage && 'mt-3 border-t border-slate-100'
                )}
              >
                {loadingChat && conv.messages.length === 0 ? (
                  <div className="space-y-3" aria-label="Loading your chat">
                    <div className="ml-auto h-10 w-2/3 animate-pulse rounded-2xl bg-slate-200/70" />
                    <div className="h-24 w-5/6 animate-pulse rounded-2xl bg-slate-200/70" />
                  </div>
                ) : conv.messages.length === 0 ? (
                  <div className="flex flex-col gap-[22px] pt-2">
                    <div className="flex flex-col items-center gap-2.5 text-center">
                      <BotAvatar size="lg" />
                      <h3 className="mt-1 text-[19px] font-bold tracking-tight text-slate-900">
                        How can I help{firstName ? `, ${firstName}` : ''}?
                      </h3>
                      <p className="max-w-[330px] text-[13.5px] leading-relaxed text-slate-600">
                        {context
                          ? 'Ask about the results on this page, your food plan, or anything about NutriLens.'
                          : 'Ask about your blood test results, Indian foods for a nutrient, or how to use NutriLens.'}
                      </p>
                    </div>
                    <div className="space-y-2.5">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500">Try asking</p>
                      <div className="grid grid-cols-2 gap-2.5">
                        {starters.map(({ icon: Icon, title, ask }) => (
                          <button
                            key={ask}
                            type="button"
                            onClick={() => send(ask)}
                            disabled={busy}
                            className="flex min-h-[108px] flex-col gap-2 rounded-[14px] border border-slate-200 bg-white p-3.5 text-left transition hover:border-brand-200 hover:bg-brand-50/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-60"
                          >
                            <span className="flex h-[30px] w-[30px] items-center justify-center rounded-[9px] bg-brand-50 text-brand-600">
                              <Icon className="h-4 w-4" aria-hidden />
                            </span>
                            <span className="text-[13.5px] font-semibold text-slate-900">{title}</span>
                            <span className="text-[12.5px] leading-snug text-slate-600">{ask}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                    <p className="flex items-center justify-center gap-1.5 text-xs text-slate-500">
                      <Lock className="h-3.5 w-3.5" aria-hidden />
                      {signedIn ? (
                        'Signed in · your chats are saved to your account'
                      ) : (
                        <span>
                          Chats aren't saved.{' '}
                          <Link to="/login" className="font-semibold text-brand-700 underline-offset-2 hover:underline">
                            Log in
                          </Link>{' '}
                          to keep them.
                        </span>
                      )}
                    </p>
                  </div>
                ) : (
                  <>
                    {conv.resumedAt && (
                      <div className="flex items-center gap-2.5" role="separator">
                        <span className="h-px flex-1 bg-slate-200" />
                        <span className="text-[11.5px] font-medium text-slate-500">
                          Continued from {shortDay(conv.resumedAt)}, {time(conv.resumedAt)}
                        </span>
                        <span className="h-px flex-1 bg-slate-200" />
                      </div>
                    )}
                    {conv.messages.map((m) =>
                      m.role === 'user' ? (
                        <div
                          key={m.id}
                          className="ml-auto w-fit max-w-[80%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-brand-600 px-3.5 py-2.5 text-sm leading-relaxed text-white max-sm:text-[15px]"
                        >
                          {m.text}
                        </div>
                      ) : m.kind === 'safety' ? (
                        <SafetyCard key={m.id} text={m.text} />
                      ) : m.kind === 'error' ? (
                        <div
                          key={m.id}
                          className="ml-[38px] flex items-center gap-3 rounded-[14px] border border-amber-200 bg-amber-50 px-3.5 py-3"
                        >
                          <CircleAlert className="h-[18px] w-[18px] shrink-0 text-amber-800" aria-hidden />
                          <p className="flex-1 text-[13.5px] leading-snug text-amber-900">{m.text}</p>
                          {m.retry && (
                            <button
                              type="button"
                              onClick={() => send(m.retry!, { resend: m.id })}
                              disabled={busy}
                              className="h-[34px] shrink-0 rounded-[9px] border border-amber-300 bg-white px-3 text-[13px] font-semibold text-amber-800 hover:bg-amber-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 disabled:opacity-50"
                            >
                              Retry
                            </button>
                          )}
                          {m.full && (
                            <button
                              type="button"
                              onClick={newChat}
                              className="h-[34px] shrink-0 rounded-[9px] border border-amber-300 bg-white px-3 text-[13px] font-semibold text-amber-800 hover:bg-amber-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500"
                            >
                              New chat
                            </button>
                          )}
                        </div>
                      ) : (
                        <div key={m.id} className="space-y-2">
                          <div className="flex items-start gap-2.5">
                            <BotAvatar />
                            <div className="min-w-0 flex-1 space-y-1">
                              <article className="break-words rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-3.5 text-sm leading-relaxed text-slate-700 max-sm:text-[15px]">
                                <RichAnswer text={m.text} />
                              </article>
                              <div className="flex items-center gap-1 pl-0.5">
                                <button
                                  type="button"
                                  onClick={() => copy(m)}
                                  className="flex h-7 items-center gap-1.5 rounded-lg px-2 text-xs text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                                >
                                  {copied === m.id ? (
                                    <Check className="h-3.5 w-3.5 text-brand-600" aria-hidden />
                                  ) : (
                                    <Copy className="h-3.5 w-3.5" aria-hidden />
                                  )}
                                  {copied === m.id ? 'Copied' : 'Copy'}
                                </button>
                                <span className="text-xs text-slate-500">· {time(m.at)}</span>
                              </div>
                            </div>
                          </div>
                          {m === lastBot && !busy && m.suggestions && m.suggestions.length > 0 && (
                            <div className="space-y-2 pl-[38px]">
                              <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500">
                                Ask next
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {m.suggestions.map((s) => (
                                  <button
                                    key={s}
                                    type="button"
                                    onClick={() => send(s)}
                                    className="min-h-[34px] rounded-full border border-brand-200 bg-white px-3 py-1.5 text-left text-[13px] font-medium text-brand-700 transition hover:border-brand-300 hover:bg-brand-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 max-sm:min-h-[40px] max-sm:text-sm"
                                  >
                                    {s}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    )}
                    {busy && (
                      <div className="flex items-center gap-2.5">
                        <BotAvatar />
                        <span
                          className="flex gap-1.5 rounded-2xl rounded-tl-md border border-slate-200 bg-white px-3.5 py-3"
                          aria-label="Assistant is typing"
                        >
                          {[0, 150, 300].map((delay) => (
                            <span
                              key={delay}
                              className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400"
                              style={{ animationDelay: `${delay}ms` }}
                            />
                          ))}
                        </span>
                      </div>
                    )}
                  </>
                )}
              </div>

              <form
                className="space-y-2 border-t border-slate-100 bg-white px-3.5 pb-3.5 pt-3 max-sm:pb-5"
                onSubmit={(e) => {
                  e.preventDefault();
                  void send(input);
                }}
              >
                <div className="flex items-end gap-2 rounded-[14px] border border-slate-300 bg-white py-1.5 pl-3.5 pr-1.5 transition focus-within:border-brand-400 focus-within:ring-4 focus-within:ring-brand-50">
                  <label htmlFor="nl-assistant-input" className="sr-only">
                    Ask a question
                  </label>
                  <textarea
                    id="nl-assistant-input"
                    ref={inputRef}
                    rows={1}
                    value={input}
                    maxLength={MAX_LENGTH}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={onKeyDown}
                    placeholder={linkedToPage ? 'Ask about these results' : 'Ask about a test, a food or your plan'}
                    className="max-h-28 min-h-[36px] flex-1 resize-none border-0 bg-transparent px-0 py-2 text-base leading-5 text-slate-900 placeholder:text-slate-500 focus:outline-none focus:ring-0 sm:text-sm"
                  />
                  <button
                    type="submit"
                    disabled={!input.trim() || busy}
                    aria-label="Send message"
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-brand-600 text-white transition hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500 max-sm:h-11 max-sm:w-11"
                  >
                    <ArrowUp className="h-[18px] w-[18px]" aria-hidden />
                  </button>
                </div>
                <p className="text-center text-[11.5px] text-slate-500">
                  {input.length > MAX_LENGTH - 80
                    ? `${MAX_LENGTH - input.length} characters left`
                    : 'General guidance from NutriLens, not medical advice.'}
                </p>
              </form>
            </>
          )}
        </section>
      )}
    </>
  );
};
