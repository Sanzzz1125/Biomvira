import {
  AddAdminResult, AdminStats, AdminUser, AuditEntry, FullAnalysisResponse, HistoryItem, Invite,
  InviteCreated, LinkCreated, LinkInfo, Paged, User,
} from '../types';
import { apiFetch, apiJson } from './http';

/* ------------------------------------------------------------------ auth */

export const authApi = {
  me: () => apiJson<User>('/auth/me'),
  session: () => apiJson<{ user: User | null }>('/auth/session'),
  login: (email: string, password: string) =>
    apiJson<User>('/auth/login', { method: 'POST', json: { email, password } }),
  register: (name: string, email: string, password: string) =>
    apiJson<User>('/auth/register', { method: 'POST', json: { name, email, password } }),
  logout: () => apiFetch('/auth/logout', { method: 'POST' }),
  updateProfile: (name: string) => apiJson<User>('/auth/me', { method: 'PATCH', json: { name } }),
  changePassword: (current_password: string, new_password: string) =>
    apiJson<User>('/auth/change-password', { method: 'POST', json: { current_password, new_password } }),
  deleteAccount: (password: string) =>
    apiFetch('/auth/delete-account', { method: 'POST', json: { password } }),
  inviteInfo: (token: string) => apiJson<LinkInfo>(`/auth/invites/${encodeURIComponent(token)}`),
  acceptInvite: (token: string, name: string, password: string) =>
    apiJson<User>(`/auth/invites/${encodeURIComponent(token)}/accept`, {
      method: 'POST', json: { name, password },
    }),
  resetInfo: (token: string) => apiJson<LinkInfo>(`/auth/reset/${encodeURIComponent(token)}`),
  resetPassword: (token: string, password: string) =>
    apiJson<User>(`/auth/reset/${encodeURIComponent(token)}`, { method: 'POST', json: { password } }),
};

/* ------------------------------------------------------------------ history */

export const historyApi = {
  list: (page = 1, pageSize = 12) =>
    apiJson<Paged<HistoryItem>>(`/history?page=${page}&page_size=${pageSize}`),
  get: (id: string) => apiJson<FullAnalysisResponse>(`/history/${encodeURIComponent(id)}`),
  remove: (id: string) => apiFetch(`/history/${encodeURIComponent(id)}`, { method: 'DELETE' }),
};

/* ------------------------------------------------------------------ admin */

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== '') search.set(k, String(v));
  });
  const s = search.toString();
  return s ? `?${s}` : '';
}

export const adminApi = {
  stats: () => apiJson<AdminStats>('/admin/stats'),
  users: (params: { q?: string; role?: string; status?: string; page?: number; page_size?: number }) =>
    apiJson<Paged<AdminUser>>(`/admin/users${query(params)}`),
  updateUser: (id: string, body: { name?: string; email?: string; status?: 'active' | 'disabled' }) =>
    apiJson<AdminUser>(`/admin/users/${id}`, { method: 'PATCH', json: body }),
  unlock: (id: string) => apiJson<AdminUser>(`/admin/users/${id}/unlock`, { method: 'POST' }),
  signOut: (id: string) => apiJson<AdminUser>(`/admin/users/${id}/sign-out`, { method: 'POST' }),
  resetLink: (id: string) => apiJson<LinkCreated>(`/admin/users/${id}/reset-link`, { method: 'POST' }),
  deleteUser: (id: string) => apiFetch(`/admin/users/${id}`, { method: 'DELETE' }),
  addAdmin: (email: string, password: string) =>
    apiJson<AddAdminResult>('/admin/access', { method: 'POST', json: { email, password } }),
  removeAdmin: (id: string) => apiJson<AdminUser>(`/admin/access/${id}`, { method: 'DELETE' }),
  transferOwnership: (user_id: string, password: string) =>
    apiJson<User>('/admin/transfer-ownership', { method: 'POST', json: { user_id, password } }),
  invites: (role?: 'user' | 'admin') => apiJson<Invite[]>(`/admin/invites${query({ role })}`),
  createInvite: (email: string, role: 'user' | 'admin' = 'user') =>
    apiJson<InviteCreated>('/admin/invites', { method: 'POST', json: { email, role } }),
  renewInvite: (id: string) => apiJson<InviteCreated>(`/admin/invites/${id}/renew`, { method: 'POST' }),
  revokeInvite: (id: string) => apiFetch(`/admin/invites/${id}`, { method: 'DELETE' }),
  auditLogs: (params: { category?: string; q?: string; page?: number; page_size?: number }) =>
    apiJson<Paged<AuditEntry>>(`/admin/audit-logs${query(params)}`),
};

/** Full shareable URL for a one-time invite or reset path returned by the API. */
export const absoluteLink = (path: string) => `${window.location.origin}${path}`;
