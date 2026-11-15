import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, FileText, UserPlus, Users } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { Skeleton } from '../../components/brand';
import { Alert, Card, PageHeader, cx } from '../../components/ui';
import { relativeTime } from '../../lib/format';
import { adminApi } from '../../services/accounts';
import { AdminStats, AuditEntry } from '../../types';
import { ActionBadge } from './shared';

const compact = new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 });
const shortDay = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short' });
const longDay = new Intl.DateTimeFormat('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });

/* ------------------------------------------------------------------ stat tile */

const StatTile: React.FC<{ label: string; value: number; caption?: React.ReactNode; icon: React.ElementType }> = ({
  label,
  value,
  caption,
  icon: Icon,
}) => (
  <Card className="p-5">
    <div className="flex items-start justify-between gap-3">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <Icon className="h-4 w-4 text-slate-400" aria-hidden />
    </div>
    <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{compact.format(value)}</p>
    {caption && <p className="mt-1 text-xs text-slate-500">{caption}</p>}
  </Card>
);

/* ------------------------------------------------------------------ daily bar chart */

/** A round axis maximum whose half is also a whole number (counts never show 2.5). */
function niceMax(value: number): number {
  if (value <= 4) return 4;
  const magnitude = 10 ** Math.max(0, Math.floor(Math.log10(value)) - 1);
  const nice = [4, 6, 8, 10, 20, 30, 40, 50, 60, 80, 100].find((n) => n * magnitude >= value);
  return (nice ?? 100) * magnitude;
}

const DailyBars: React.FC<{ title: string; unit: string; days: { date: string; value: number }[] }> = ({ title, unit, days }) => {
  const [active, setActive] = useState<number | null>(null);
  const total = days.reduce((sum, d) => sum + d.value, 0);
  const peak = Math.max(...days.map((d) => d.value));
  const top = niceMax(peak);
  const ticks = [top, top / 2, 0];
  const peakIndex = peak > 0 ? days.map((d) => d.value).lastIndexOf(peak) : -1;
  const labelled = new Set([0, 4, 9, days.length - 1]);
  const dayLabel = (iso: string, i: number) => (i === days.length - 1 ? 'Today' : shortDay.format(new Date(`${iso}T00:00:00`)));

  return (
    <Card className="p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="text-sm text-slate-500">
          <span className="font-semibold text-slate-900">{total}</span> in 14 days
        </p>
      </div>

      <div className="mt-5 flex gap-3">
        {/* y axis */}
        <div className="relative h-44 w-6 shrink-0 text-right text-[11px] tabular-nums text-slate-400" aria-hidden>
          {ticks.map((t, i) => (
            <span key={t} className="absolute right-0 -translate-y-1/2" style={{ top: `${(i / (ticks.length - 1)) * 100}%` }}>
              {t}
            </span>
          ))}
        </div>

        <div className="min-w-0 flex-1">
          {/* plot */}
          <div className="relative h-44" role="img" aria-label={`${title}: ${total} over the last 14 days. Table view below.`}>
            {ticks.map((t, i) => (
              <div
                key={t}
                className={cx('absolute inset-x-0 h-px', t === 0 ? 'bg-slate-300' : 'bg-slate-100')}
                style={{ top: `${(i / (ticks.length - 1)) * 100}%` }}
              />
            ))}
            <div className="absolute inset-0 flex">
              {days.map((d, i) => {
                const height = top ? (d.value / top) * 100 : 0;
                const isActive = active === i;
                return (
                  <div
                    key={d.date}
                    className="relative flex h-full flex-1 cursor-default items-end justify-center outline-none"
                    tabIndex={0}
                    aria-label={`${longDay.format(new Date(`${d.date}T00:00:00`))}: ${d.value} ${unit}`}
                    onPointerEnter={() => setActive(i)}
                    onPointerLeave={() => setActive(null)}
                    onFocus={() => setActive(i)}
                    onBlur={() => setActive(null)}
                  >
                    {d.value > 0 && (
                      <div
                        className={cx('w-[62%] max-w-[24px] rounded-t transition-colors', isActive ? 'bg-brand-600' : 'bg-brand-500')}
                        style={{ height: `${height}%` }}
                      />
                    )}
                    {i === peakIndex && !isActive && (
                      <span
                        className="pointer-events-none absolute text-[11px] font-semibold text-slate-700"
                        style={{ bottom: `calc(${height}% + 4px)` }}
                      >
                        {d.value}
                      </span>
                    )}
                    {isActive && (
                      <div
                        role="tooltip"
                        className="pointer-events-none absolute z-10 whitespace-nowrap rounded-lg border border-slate-200 bg-white px-3 py-2 text-left shadow-card-lg"
                        style={{
                          bottom: `calc(${height}% + 8px)`,
                          ...(i > days.length - 4 ? { right: 0 } : i < 3 ? { left: 0 } : {}),
                        }}
                      >
                        <p className="text-sm font-semibold text-slate-900">
                          {d.value} {unit}
                        </p>
                        <p className="text-xs text-slate-500">{longDay.format(new Date(`${d.date}T00:00:00`))}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          {/* x axis */}
          <div className="mt-2 flex text-[11px] text-slate-400" aria-hidden>
            {days.map((d, i) => (
              <span key={d.date} className="flex-1 whitespace-nowrap text-center">
                {labelled.has(i) ? dayLabel(d.date, i) : ''}
              </span>
            ))}
          </div>
        </div>
      </div>

      <details className="mt-4 text-sm">
        <summary className="cursor-pointer text-xs font-medium text-slate-500 hover:text-slate-700">View as table</summary>
        <table className="mt-2 w-full text-left text-xs">
          <thead className="text-slate-500">
            <tr>
              <th className="py-1 font-medium">Day</th>
              <th className="py-1 text-right font-medium capitalize">{unit}</th>
            </tr>
          </thead>
          <tbody className="tabular-nums text-slate-700">
            {days.map((d) => (
              <tr key={d.date} className="border-t border-slate-100">
                <td className="py-1">{longDay.format(new Date(`${d.date}T00:00:00`))}</td>
                <td className="py-1 text-right">{d.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </Card>
  );
};

/* ------------------------------------------------------------------ page */

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [recent, setRecent] = useState<AuditEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminApi.stats().then(setStats).catch((err: Error) => setError(err.message));
    adminApi.auditLogs({ page_size: 6 }).then((p) => setRecent(p.items)).catch(() => setRecent([]));
  }, []);

  const roles = stats?.users_by_role;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Admin portal"
        title={`Welcome, ${user?.name.split(' ')[0] ?? 'admin'}`}
        description="An overview of accounts and activity. Medical report contents are never shown here."
      />
      {error && <Alert tone="error">{error}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats && roles ? (
          <>
            <StatTile
              label="Total accounts"
              value={stats.users_total}
              icon={Users}
              caption={`${roles.owner} owner · ${roles.admin} admin${roles.admin === 1 ? '' : 's'} · ${roles.user} user${roles.user === 1 ? '' : 's'}${stats.users_disabled ? ` · ${stats.users_disabled} disabled` : ''}`}
            />
            <StatTile label="New accounts" value={stats.signups_last_7_days} icon={UserPlus} caption="Last 7 days" />
            <StatTile label="Saved analyses" value={stats.reports_total} icon={FileText} caption="All time, across all accounts" />
            <StatTile label="Analyses this week" value={stats.reports_last_7_days} icon={FileText} caption="Last 7 days" />
          </>
        ) : (
          [0, 1, 2, 3].map((i) => (
            <Card key={i} className="space-y-3 p-5">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-8 w-1/3" />
              <Skeleton className="h-3 w-2/3" />
            </Card>
          ))
        )}
      </div>

      {stats && (
        <div className="grid gap-6 xl:grid-cols-2">
          <DailyBars title="Saved analyses per day" unit="analyses" days={stats.daily.map((d) => ({ date: d.date, value: d.analyses }))} />
          <DailyBars title="New accounts per day" unit="sign-ups" days={stats.daily.map((d) => ({ date: d.date, value: d.signups }))} />
        </div>
      )}

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h3 className="text-base font-semibold">Recent activity</h3>
          <Link to="/admin/audit" className="inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:text-brand-800">
            Full audit log <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </div>
        {!recent ? (
          <div className="space-y-3 p-5">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-5/6" />
          </div>
        ) : recent.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-slate-500">No activity yet.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {recent.map((entry) => (
              <li key={entry.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
                <div className="flex min-w-0 flex-wrap items-center gap-2 text-sm">
                  <ActionBadge action={entry.action} />
                  <span className="truncate text-slate-700">{entry.actor_email ?? entry.target_email ?? 'System'}</span>
                  {entry.actor_email && entry.target_email && entry.target_email !== entry.actor_email && (
                    <span className="truncate text-slate-500">→ {entry.target_email}</span>
                  )}
                </div>
                <span className="text-xs text-slate-500">{relativeTime(entry.created_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
};
