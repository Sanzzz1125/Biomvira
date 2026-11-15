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
  if (status >= 500) return 'Something went wrong on our side. Please try again.';
  return 'Request failed. Please try again.';
}

type ApiInit = Omit<RequestInit, 'body'> & { json?: unknown; body?: BodyInit };

export async function apiFetch(path: string, init: ApiInit = {}): Promise<Response> {
  const { json, headers, ...rest } = init;
  const method = (rest.method || 'GET').toUpperCase();
  const finalHeaders = new Headers(headers);
  if (json !== undefined) finalHeaders.set('Content-Type', 'application/json');
  if (UNSAFE.has(method)) {
    const csrf = readCookie('nl_csrf');
    if (csrf) finalHeaders.set('X-CSRF-Token', csrf);
  }

  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      ...rest,
      method,
      headers: finalHeaders,
      body: json !== undefined ? JSON.stringify(json) : rest.body,
      credentials: 'same-origin',
    });
  } catch (err) {
    if ((err as Error)?.name === 'TimeoutError' || (err as Error)?.name === 'AbortError') throw err;
    throw new ApiError('Could not reach the server. Check your connection and try again.', 0);
  }

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
