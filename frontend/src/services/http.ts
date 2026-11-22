/** Small fetch wrapper: same-origin cookies, CSRF header on changes, friendly errors. */

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const UNSAFE = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.split('; ').find((c) => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : null;
}

function messageFrom(data: unknown, status: number): string {
  const detail = (data as { detail?: unknown })?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0] as { msg?: string; loc?: string[] };
    const field = first.loc?.[first.loc.length - 1];
    if (field === 'email') return 'Enter a valid email address.';
    if (first.msg) return first.msg.replace(/^Value error, /, '');
  }
  if (status === 401) return 'Please sign in to continue.';
  if (status === 403) return "You don't have permission to do that.";
  if (status === 404) return 'Not found.';
  if (status === 429) return 'Too many attempts. Please wait a minute and try again.';
  if (GATEWAY.has(status)) return 'The server is taking too long to respond. Please try again in a minute.';
  if (status >= 500) return 'Something went wrong on our side. Please try again.';
  return 'Request failed. Please try again.';
}

type ApiInit = Omit<RequestInit, 'body'> & { json?: unknown; body?: BodyInit };

// The free API server sleeps when idle and takes up to a minute to wake. While it wakes, requests fail with a
// network error or a gateway status (502/503/504), so those are retried for up to WAKE_LIMIT_MS instead of being
// shown as errors. Genuine application errors (500 and below) are never retried.
const WAKE_LIMIT_MS = 90_000;
const GATEWAY = new Set([502, 503, 504]);
export const WAKE_EVENT = 'biomvira:server-waking';

function announceWaking(waking: boolean) {
  if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent(WAKE_EVENT, { detail: waking }));
}

const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function apiFetch(path: string, init: ApiInit = {}): Promise<Response> {
  const { json, headers, ...rest } = init;
  const method = (rest.method || 'GET').toUpperCase();
  const finalHeaders = new Headers(headers);
  if (json !== undefined) finalHeaders.set('Content-Type', 'application/json');
  if (UNSAFE.has(method)) {
    const csrf = readCookie('nl_csrf');
    if (csrf) finalHeaders.set('X-CSRF-Token', csrf);
  }

  const started = Date.now();
  let response: Response | null = null;
  let waited = false;
  for (let attempt = 0; ; attempt++) {
    let failed = false;
    try {
      response = await fetch(`/api/v1${path}`, {
        ...rest,
        method,
        headers: finalHeaders,
        body: json !== undefined ? JSON.stringify(json) : rest.body,
        credentials: 'same-origin',
      });
      failed = GATEWAY.has(response.status);
    } catch (err) {
      if ((err as Error)?.name === 'TimeoutError' || (err as Error)?.name === 'AbortError') throw err;
      failed = true;
      response = null;
    }
    if (!failed) break;
    if (Date.now() - started > WAKE_LIMIT_MS) {
      announceWaking(false);
      if (!response) throw new ApiError('Could not reach the server. Check your connection and try again.', 0);
      break;
    }
    waited = true;
    announceWaking(true);
    await pause(Math.min(2000 * (attempt + 1), 8000));
  }
  if (waited) announceWaking(false);
  if (!response) throw new ApiError('Could not reach the server. Check your connection and try again.', 0);

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(messageFrom(data, response.status), response.status);
  }
  return response;
}

export async function apiJson<T>(path: string, init: ApiInit = {}): Promise<T> {
  const response = await apiFetch(path, init);
  return response.json() as Promise<T>;
}
