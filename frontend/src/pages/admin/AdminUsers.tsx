import React, { useCallback, useEffect, useState } from 'react';
import { Search, UserPlus, Users } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { Avatar, EmptyState, RoleBadge, Skeleton } from '../../components/brand';
import { SelectField } from '../../components/forms';
import { Alert, Button, Card, PageHeader } from '../../components/ui';
import { formatDate, relativeTime } from '../../lib/format';
import { adminApi } from '../../services/accounts';
import { AdminUser, Paged } from '../../types';
import { AccountStatus, InviteDialog, Pagination, PendingInvites, UserActions } from './shared';

const PAGE_SIZE = 20;

export const AdminUsers: React.FC = () => {
  const { user: viewer } = useAuth();
  const isOwner = viewer?.role === 'owner';
  const [q, setQ] = useState('');
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paged<AdminUser> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inviting, setInviting] = useState(false);
  const [inviteKey, setInviteKey] = useState(0);

  // Debounce typing in the search box.
  useEffect(() => {
    const t = window.setTimeout(() => {
      setSearch(q.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(t);
  }, [q]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await adminApi.users({ q: search, role, status, page, page_size: PAGE_SIZE }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [search, role, status, page]);

  useEffect(() => {
    load();
  }, [load]);

  const replace = (updated: AdminUser) =>
    setData((d) => d && { ...d, items: d.items.map((u) => (u.id === updated.id ? { ...u, ...updated } : u)) });
  const removeRow = (id: string) => setData((d) => d && { ...d, items: d.items.filter((u) => u.id !== id), total: d.total - 1 });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin portal"
        title="Users"
        description={
          isOwner
            ? 'Manage every account. As the owner you can also manage admins.'
            : 'Manage user accounts. Only the owner can change admin accounts.'
        }
        actions={
          <Button icon={<UserPlus className="h-4 w-4" aria-hidden />} onClick={() => setInviting(true)}>
            Invite someone
          </Button>
        }
      />

      {/* Filters: one row above the table they scope */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="relative flex-1">
          <label htmlFor="user-search" className="sr-only">
            Search by name or email
          </label>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            id="user-search"
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by name or email"
            className="field h-10 pl-9"
          />
        </div>
        <SelectField label="Role" hideLabel value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }} className="sm:w-40">
          <option value="">All roles</option>
          <option value="owner">Owner</option>
          <option value="admin">Admins</option>
          <option value="user">Users</option>
        </SelectField>
        <SelectField label="Status" hideLabel value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="sm:w-40">
          <option value="">Any status</option>
          <option value="active">Active</option>
          <option value="disabled">Disabled</option>
        </SelectField>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      <Card className="overflow-hidden">
        {!data && loading ? (
          <div className="space-y-4 p-5">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </div>
        ) : data && data.items.length === 0 ? (
          <EmptyState icon={Users} title="No accounts found" description="Try a different search or filter." />
        ) : (
          data && (
            <div className={loading ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    <tr>
                      <th scope="col" className="py-3 pl-4 pr-2 sm:px-5">Account</th>
                      <th scope="col" className="px-2 py-3 sm:px-3">Role</th>
                      <th scope="col" className="hidden px-3 py-3 sm:table-cell">Status</th>
                      <th scope="col" className="hidden px-3 py-3 text-right md:table-cell">Reports</th>
                      <th scope="col" className="hidden px-3 py-3 lg:table-cell">Joined</th>
                      <th scope="col" className="hidden px-3 py-3 md:table-cell">Last login</th>
                      <th scope="col" className="w-12 px-2 py-3 sm:px-3"><span className="sr-only">Actions</span></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.items.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-50/60">
                        <td className="py-3 pl-4 pr-2 sm:px-5">
                          <div className="flex items-center gap-3">
                            <span className="hidden sm:block">
                              <Avatar name={u.name} />
                            </span>
                            <div className="min-w-0 max-w-[10rem] sm:max-w-[16rem]">
                              <p className="truncate font-medium text-slate-900">
                                {u.name}
                                {u.id === viewer?.id && <span className="ml-1.5 text-xs font-normal text-slate-500">(you)</span>}
                              </p>
                              <p className="truncate text-xs text-slate-500">{u.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-2 py-3 sm:px-3">
                          <RoleBadge role={u.role} />
                          <div className="mt-1.5 sm:hidden">
                            <AccountStatus user={u} />
                          </div>
                        </td>
                        <td className="hidden px-3 py-3 sm:table-cell"><AccountStatus user={u} /></td>
                        <td className="hidden px-3 py-3 text-right tabular-nums text-slate-700 md:table-cell">{u.report_count}</td>
                        <td className="hidden px-3 py-3 text-slate-600 lg:table-cell">{formatDate(u.created_at)}</td>
                        <td className="hidden px-3 py-3 text-slate-600 md:table-cell">{relativeTime(u.last_login_at)}</td>
                        <td className="px-2 py-3 text-right sm:px-3">
                          <UserActions user={u} onChanged={replace} onRemoved={removeRow} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPage={setPage} />
            </div>
          )
        )}
      </Card>

      <PendingInvites role={isOwner ? undefined : 'user'} refreshKey={inviteKey} />

      <InviteDialog
        open={inviting}
        onClose={() => setInviting(false)}
        allowAdminRole={isOwner}
        onCreated={() => setInviteKey((k) => k + 1)}
      />
    </div>
  );
};
