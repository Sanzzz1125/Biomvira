import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, FileQuestion, ScanLine } from 'lucide-react';
import { EmptyState, PageSpinner } from '../components/brand';
import { ResultsView } from '../components/ResultsView';
import { useToast } from '../components/Toast';
import { Card, buttonClasses } from '../components/ui';
import { formatDateTime } from '../lib/format';
import { historyApi } from '../services/accounts';
import { downloadPlanPdf } from '../services/api';
import { FullAnalysisResponse } from '../types';

export const HistoryDetailPage: React.FC = () => {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const { notify } = useToast();
  const [result, setResult] = useState<FullAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    setResult(null);
    setError(null);
    historyApi.get(id).then(setResult).catch((err: Error) => setError(err.message));
  }, [id]);

  const download = async (dietPlan?: FullAnalysisResponse['diet_plan']) => {
    if (!result) return;
    setExporting(true);
    try {
      await downloadPlanPdf(dietPlan ? { ...result, diet_plan: dietPlan } : result);
    } catch (err) {
      notify('error', 'PDF download failed', (err as Error).message);
    } finally {
      setExporting(false);
    }
  };

  if (error) {
    return (
      <Card className="mx-auto max-w-2xl">
        <EmptyState
          icon={FileQuestion}
          title="Report not found"
          description="It may have been deleted, or it belongs to a different account."
          action={
            <Link to="/history" className={buttonClasses('secondary')}>
              Back to my reports
            </Link>
          }
        />
      </Card>
    );
  }
  if (!result) return <PageSpinner label="Loading report…" />;

  return (
    <div className="space-y-6">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
        <Link
          to="/history"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 transition-colors hover:text-slate-900"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden /> Back to my reports
        </Link>
        <p className="text-sm text-slate-500">Saved {formatDateTime(result.timestamp)}</p>
      </div>
      <ResultsView
        result={result}
        profile={result.user_profile}
        isExporting={exporting}
        onDownload={download}
        onReset={() => navigate('/')}
        resetLabel="Analyze another report"
        resetIcon={<ScanLine className="h-4 w-4" aria-hidden />}
        savedReportId={id}
      />
    </div>
  );
};
