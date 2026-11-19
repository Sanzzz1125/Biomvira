import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, BookmarkCheck, FileCheck2, UserPlus } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { AnalysisLoadingModal } from '../components/AnalysisLoadingModal';
import { ResultsView } from '../components/ResultsView';
import { Stepper } from '../components/Stepper';
import { Alert, Button, Card } from '../components/ui';
import { UploadZone } from '../components/UploadZone';
import { UserProfileForm } from '../components/UserProfileForm';
import { VerificationTable } from '../components/VerificationTable';
import { Analyzer, Step } from '../hooks/useAnalyzer';

const STEPS: { id: Step; label: string }[] = [
  { id: 'upload', label: 'Upload report' },
  { id: 'profile', label: 'Your profile' },
  { id: 'results', label: 'Your plan' },
];
// The review step is only part of the journey when a result needs attention.
const REVIEW_STEPS: { id: Step; label: string }[] = [STEPS[0], { id: 'verify', label: 'Review results' }, ...STEPS.slice(1)];

const ReportSummary: React.FC<{ count: number; notes: string[]; onReview: () => void }> = ({ count, notes, onReview }) => (
  <Card className="mx-auto flex max-w-3xl flex-col gap-4 p-5 sm:flex-row sm:items-start sm:justify-between">
    <div className="flex items-start gap-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
        <FileCheck2 className="h-[18px] w-[18px]" aria-hidden />
      </span>
      <div>
        <p className="text-[15px] font-semibold text-slate-900">
          {count} {count === 1 ? 'result' : 'results'} read from your report
        </p>
        {notes.length > 0 ? (
          <ul className="mt-1 space-y-1 text-sm text-slate-600">
            {notes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-0.5 text-sm text-slate-500">Values, units and reference ranges were read automatically.</p>
        )}
      </div>
    </div>
    <Button variant="secondary" size="sm" onClick={onReview} className="shrink-0 self-start">
      View or edit results
    </Button>
  </Card>
);

const SaveNotice: React.FC<{ saved: boolean }> = ({ saved }) => {
  const { user } = useAuth();
  if (saved) {
    return (
      <Alert tone="info" icon={<BookmarkCheck className="h-4 w-4" aria-hidden />} className="">
        All your reports are stored in History.{' '}
        <Link to="/history" className="font-semibold underline-offset-2 hover:underline">
          View history
        </Link>
      </Alert>
    );
  }
  if (user) return null;
  return (
    <Alert tone="warning" icon={<UserPlus className="h-4 w-4" aria-hidden />} className="">
      This result isn't saved because you're browsing as a guest.{' '}
      <Link to="/register" className="font-semibold underline-offset-2 hover:underline">
        Create a free account
      </Link>{' '}
      or{' '}
      <Link to="/login" className="font-semibold underline-offset-2 hover:underline">
        log in
      </Link>{' '}
      to keep future analyses in your history.
    </Alert>
  );
};

export const AnalyzerPage: React.FC<{ analyzer: Analyzer }> = ({ analyzer }) => {
  const { step } = analyzer;
  const [reviewed, setReviewed] = React.useState(false);
  useEffect(() => {
    if (step === 'verify') setReviewed(true);
    if (step === 'upload') setReviewed(false);
  }, [step]);
  const steps = reviewed ? REVIEW_STEPS : STEPS;
  const currentStepIdx = steps.findIndex((s) => s.id === step);

  useEffect(() => {
    window.scrollTo?.({ top: 0, behavior: 'smooth' });
  }, [step]);

  return (
    <div className="space-y-10">
      <div id="analyze" className="mx-auto max-w-3xl scroll-mt-24">
        <Stepper steps={steps} currentIndex={currentStepIdx} />
      </div>

      {analyzer.error && (
        <Alert
          className="mx-auto max-w-3xl"
          icon={<AlertTriangle className="h-4 w-4" aria-hidden />}
          title="Something went wrong"
        >
          {analyzer.error}
        </Alert>
      )}

      <div key={step} className="animate-fade-up">
        {step === 'upload' && (
          <UploadZone
            onExtractionComplete={analyzer.handleExtractionComplete}
            isLoading={analyzer.isLoading}
            setIsLoading={analyzer.setIsLoading}
          />
        )}

        {step === 'verify' && (
          <VerificationTable
            markers={analyzer.extractedMarkers}
            setMarkers={analyzer.setExtractedMarkers}
            sanitizedPreview={analyzer.sanitizedPreview}
            warnings={analyzer.extractionWarnings}
            onProceedToProfile={() => analyzer.setStep('profile')}
            onReset={analyzer.reset}
          />
        )}

        {step === 'profile' && (
          <div className="space-y-6">
          <ReportSummary
            count={analyzer.extractedMarkers.length}
            notes={analyzer.extractionWarnings}
            onReview={() => analyzer.setStep('verify')}
          />
          <UserProfileForm
            profile={analyzer.userProfile}
            setProfile={analyzer.setUserProfile}
            onSubmit={analyzer.handleRunAnalysis}
            onBack={() => analyzer.setStep('verify')}
            isLoading={analyzer.isLoading}
          />
          </div>
        )}

        {step === 'results' && analyzer.analysisResult && (
          <div className="space-y-6">
            <SaveNotice saved={!!analyzer.analysisResult.saved_to_history} />
            <ResultsView
              result={analyzer.analysisResult}
              profile={analyzer.userProfile}
              isExporting={analyzer.isExportingPdf}
              onDownload={analyzer.handleDownloadPdf}
              onReset={analyzer.reset}
              savedReportId={analyzer.analysisResult.saved_to_history ? analyzer.analysisResult.analysis_id : null}
            />
          </div>
        )}
      </div>


      <AnalysisLoadingModal
        isOpen={analyzer.isAnalyzing}
        profile={analyzer.userProfile}
        markerCount={analyzer.extractedMarkers.length}
      />
    </div>
  );
};
