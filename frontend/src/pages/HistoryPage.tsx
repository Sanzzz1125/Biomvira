import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, FileText, Lock, Plus, Stethoscope, Trash2 } from 'lucide-react';
import { useAuth, wasSignedIn } from '../auth/AuthContext';
import { EmptyState, PageSpinner, Skeleton } from '../components/brand';
import { ConfirmDialog } from '../components/Modal';
import { useToast } from '../components/Toast';
import { Alert, Badge, Button, Card, PageHeader, STATUS_META, buttonClasses, cx } from '../components/ui';
import { formatDateTime, relativeTime } from '../lib/format';
import { historyApi } from '../services/accounts';
import { HistoryItem, MarkerStatus } from '../types';

const PAGE_SIZE = 12;
const STATUS_ORDER: MarkerStatus[] = ['low', 'borderline', 'high', 'normal'];

const GuestPrompt: React.FC = () => (
  <div className="mx-auto max-w-5xl space-y-6">
    <PageHeader eyebrow="History" title="My reports" />
    <Card>
      <EmptyState
        icon={Lock}
        title="Sign in to see your saved reports"
        description="When you're logged in, every analysis is saved privately to your account. Only you can see your reports."
        action={
          <>
            <Link to="/login" state={{ from: '/history' }} className={buttonClasses('primary')}>
              Log in
            </Link>
            <Link to="/register" className={buttonClasses('secondary')}>
              Create a free account
            </Link>
          </>
        }
      />
    </Card>
  </div>
);

const ReportCard: React.FC<{ item: HistoryItem; onDelete: () => void }> = ({ item, onDelete }) => {
  const shown = item.markers.slice(0, 4);
  return (
    <Card className="flex flex-col p-5 transition-shadow hover:shadow-card-lg">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[15px] font-semibold text-slate-900">{formatDateTime(item.created_at)}</p>
          <p className="mt-0.5 text-xs text-slate-500">
            {relativeTime(item.created_at)} · {item.marker_count} biomarker{item.marker_count === 1 ? '' : 's'}
          </p>
        </div>
        {item.requires_consult && (
          <Badge tone="red" icon={<Stethoscope className="h-3 w-3" aria-hidden />}>
            See a doctor
          </Badge>
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {STATUS_ORDER.filter((s) => item.status_summary[s]).map((s) => (
          <Badge key={s} tone={STATUS_META[s].tone}>
            {item.status_summary[s]} {STATUS_META[s].label}
          </Badge>
        ))}
      </div>

      <ul className="mt-4 flex-1 space-y-2">
        {shown.map((m) => (
          <li key={m.biomarker_key} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex min-w-0 items-center gap-2">
              <span className={cx('h-2 w-2 shrink-0 rounded-full', STATUS_META[m.status]?.dot ?? 'bg-slate-300')} />
              <span className="truncate text-slate-700">{m.display_name}</span>
            </span>
            <span className="shrink-0 tabular-nums text-slate-500">
              {m.value} {m.unit}
            </span>
          </li>
        ))}
        {item.markers.length > shown.length && (
          <li className="text-xs text-slate-500">+{item.markers.length - shown.length} more</li>
        )}
      </ul>

      <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
        <Link
          to={`/history/${item.id}`}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-800"
        >
          View report <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
        <button
          type="button"
          onClick={onDelete}
          className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
          aria-label={`Delete report from ${formatDateTime(item.created_at)}`}
        >
          <Trash2 className="h-4 w-4" aria-hidden />
        </button>
      </div>
    </Card>
  );
};

const ReportList: React.FC = () => {
  const { notify } = useToast();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toDelete, setToDelete] = useState<HistoryItem | null>(null);

  const load = useCallback(async (nextPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await historyApi.list(nextPage, PAGE_SIZE);
      setItems((prev) => (nextPage === 1 ? data.items : [...prev, ...data.items]));
      setTotal(data.total);
      setPage(nextPage);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(1);
  }, [load]);

  const remove = async () => {
    if (!toDelete) return;
    await historyApi.remove(toDelete.id);
    setItems((prev) => prev.filter((i) => i.id !== toDelete.id));
    setTotal((t) => t - 1);
    notify('success', 'Report deleted');
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <PageHeader
        eyebrow="History"
        title="My reports"
        description={
          loading && !items.length
            ? 'Your saved analyses. Only you can see these.'
            : `${total} saved ${total === 1 ? 'analysis' : 'analyses'}. Only you can see these.`
        }
        actions={
          <Link to="/" className={buttonClasses('primary')}>
            <Plus className="h-4 w-4" aria-hidden /> New analysis
          </Link>
        }
      />

      {error && <Alert tone="error">{error}</Alert>}

      {loading && !items.length ? (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3" role="status" aria-label="Loading reports">
          {[0, 1, 2].map((i) => (
            <Card key={i} className="space-y-4 p-5">
              <Skeleton className="h-5 w-1/2" />
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-16 w-full" />
            </Card>
          ))}
        </div>
      ) : !items.length && !error ? (
        <Card>
          <EmptyState
            icon={FileText}
            title="No saved reports yet"
            description="Analyze a lab report while you're logged in and it will appear here automatically."
            action={
              <Link to="/" className={buttonClasses('primary')}>
                Analyze a report
              </Link>
            }
          />
        </Card>
      ) : (
        <>
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {items.map((item) => (
              <ReportCard key={item.id} item={item} onDelete={() => setToDelete(item)} />
            ))}
          </div>
          {items.length < total && (
            <div className="flex justify-center">
              <Button variant="secondary" loading={loading} onClick={() => load(page + 1)}>
                Load more
              </Button>
            </div>
          )}
        </>
      )}

      <ConfirmDialog
        open={!!toDelete}
        onClose={() => setToDelete(null)}
        tone="danger"
        title="Delete this report?"
        message={
          toDelete && (
            <>
              The analysis from <strong>{formatDateTime(toDelete.created_at)}</strong> will be permanently
              deleted. This can't be undone.
            </>
          )
        }
        confirmLabel="Delete report"
        onConfirm={remove}
      />
    </div>
  );
};

export const HistoryPage: React.FC = () => {
  const { user, ready } = useAuth();
  if (!ready && wasSignedIn()) return <PageSpinner />;
  return user ? <ReportList /> : <GuestPrompt />;
};
