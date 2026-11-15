import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, BookmarkCheck, UserPlus } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { AnalysisLoadingModal } from '../components/AnalysisLoadingModal';
import { Hero } from '../components/Hero';
import { ResultsView } from '../components/ResultsView';
import { Stepper } from '../components/Stepper';
import { Alert } from '../components/ui';
import { UploadZone } from '../components/UploadZone';
import { UserProfileForm } from '../components/UserProfileForm';
import { VerificationTable } from '../components/VerificationTable';
import { Analyzer, Step } from '../hooks/useAnalyzer';

const STEPS: { id: Step; label: string }[] = [
  { id: 'upload', label: 'Upload report' },
  { id: 'verify', label: 'Check results' },
  { id: 'profile', label: 'Your profile' },
  { id: 'results', label: 'Your plan' },
];

const SaveNotice: React.FC<{ saved: boolean }> = ({ saved }) => {
  const { user } = useAuth();
  if (saved) {
    return (
      <Alert tone="info" icon={<BookmarkCheck className="h-4 w-4" aria-hidden />} className="mx-auto max-w-6xl">
        All your reports are stored in History.{' '}
        <Link to="/history" className="font-semibold underline-offset-2 hover:underline">
          View history
        </Link>
      </Alert>
    );
  }
  if (user) return null;
  return (
    <Alert tone="warning" icon={<UserPlus className="h-4 w-4" aria-hidden />} className="mx-auto max-w-6xl">
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
  const currentStepIdx = STEPS.findIndex((s) => s.id === step);

  useEffect(() => {
    window.scrollTo?.({ top: 0, behavior: 'smooth' });
  }, [step]);

  return (
    <div className="space-y-10">
      {step === 'upload' && <Hero />}

      <div className="mx-auto max-w-3xl">
        <Stepper steps={STEPS} currentIndex={currentStepIdx} />
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
          <UserProfileForm
            profile={analyzer.userProfile}
            setProfile={analyzer.setUserProfile}
            onSubmit={analyzer.handleRunAnalysis}
            onBack={() => analyzer.setStep('verify')}
            isLoading={analyzer.isLoading}
          />
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
