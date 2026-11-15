import React, { useCallback, useEffect, useState } from 'react';
import { ScrollText, Search } from 'lucide-react';
import { EmptyState, Skeleton } from '../../components/brand';
import { SelectField } from '../../components/forms';
import { Alert, Card, PageHeader } from '../../components/ui';
import { formatDateTime, relativeTime } from '../../lib/format';
import { adminApi } from '../../services/accounts';
import { AuditEntry, Paged } from '../../types';
import { ActionBadge, Pagination } from './shared';

const PAGE_SIZE = 25;

const CATEGORIES = [
  { value: '', label: 'All activity' },
  { value: 'auth', label: 'Sign-ins & sign-ups' },
  { value: 'user', label: 'Account management' },
  { value: 'role', label: 'Admin access changes' },
  { value: 'owner', label: 'Ownership' },
  { value: 'invite', label: 'Invitations' },
  { value: 'reset', label: 'Password resets' },
  { value: 'account', label: 'Self-service changes' },
];

function detailText(entry: AuditEntry): string | null {
  const d = entry.details;
  if (!d) return null;
  if (Array.isArray(d.fields)) return `Changed ${(d.fields as string[]).join(' and ')}`;
  if (typeof d.role === 'string') return `Role: ${d.role}`;
  if (d.via === 'cli') return 'Via server command line';
  return null;
}

export const AdminAudit: React.FC = () => {
  const [q, setQ] = useState('');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paged<AuditEntry> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      setData(await adminApi.auditLogs({ q: search, category, page, page_size: PAGE_SIZE }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [search, category, page]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin portal"
        title="Audit log"
        description="A permanent record of sign-ins, permission changes and account actions. Entries can't be edited or deleted."
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="relative flex-1">
          <label htmlFor="audit-search" className="sr-only">
            Search by email
          </label>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            id="audit-search"
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by email"
            className="field h-10 pl-9"
          />
        </div>
        <SelectField
          label="Type of activity"
          hideLabel
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setPage(1);
          }}
          className="sm:w-56"
        >
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </SelectField>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      <Card className="overflow-hidden">
        {!data && loading ? (
          <div className="space-y-4 p-5">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-6 w-full" />
            ))}
          </div>
        ) : data && data.items.length === 0 ? (
          <EmptyState icon={ScrollText} title="No matching activity" description="Try a different search or activity type." />
        ) : (
          data && (
            <div className={loading ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    <tr>
                      <th scope="col" className="py-3 pl-4 pr-2 sm:px-5">When</th>
                      <th scope="col" className="px-2 py-3 sm:px-3">Action</th>
                      <th scope="col" className="hidden px-3 py-3 sm:table-cell">By</th>
                      <th scope="col" className="hidden px-3 py-3 md:table-cell">Affected account</th>
                      <th scope="col" className="hidden px-3 py-3 lg:table-cell">IP address</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.items.map((entry) => {
                      const detail = detailText(entry);
                      return (
                        <tr key={entry.id} className="align-top hover:bg-slate-50/60">
                          <td className="whitespace-nowrap py-3 pl-4 pr-2 sm:px-5">
                            <p className="text-slate-800">{relativeTime(entry.created_at)}</p>
                            <p className="text-xs text-slate-500">{formatDateTime(entry.created_at)}</p>
                          </td>
                          <td className="px-2 py-3 sm:px-3">
                            <ActionBadge action={entry.action} />
                            {detail && <p className="mt-1 text-xs text-slate-500">{detail}</p>}
                            <p className="mt-1 max-w-[10rem] truncate text-xs text-slate-500 sm:hidden">
                              By {entry.actor_email ?? 'not signed in'}
                            </p>
                          </td>
                          <td className="hidden max-w-[220px] truncate px-3 py-3 text-slate-700 sm:table-cell">
                            {entry.actor_email ?? <span className="text-slate-400">Not signed in</span>}
                          </td>
                          <td className="hidden max-w-[220px] truncate px-3 py-3 text-slate-700 md:table-cell">
                            {entry.target_email ?? <span className="text-slate-400">—</span>}
                          </td>
                          <td className="hidden px-3 py-3 font-mono text-xs text-slate-500 lg:table-cell">{entry.ip ?? '—'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPage={setPage} />
            </div>
          )
        )}
      </Card>
    </div>
  );
};
