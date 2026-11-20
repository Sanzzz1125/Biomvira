import { useCallback, useState } from 'react';
import { analyzeAndRecommend, downloadPlanPdf } from '../services/api';
import {
  DetectedBiomarker,
  ExtractionResponse,
  FullAnalysisResponse,
  MarkerInput,
  UserProfile,
} from '../types';
import { needsReview } from '../lib/review';

export type Step = 'upload' | 'verify' | 'profile' | 'results';

const DEFAULT_PROFILE: UserProfile = {
  age: 25, gender: 'female', diet_type: 'veg', allergens: [], height_cm: null, weight_kg: null, activity: 'sedentary',
  region: '', meats: [], custom_allergies: [], existing_diet: '',
};

/**
 * The analyzer workflow state. It lives at the app root so an in-progress analysis survives
 * moving between pages, and is cleared whenever the signed-in person changes.
 */
export function useAnalyzer() {
  const [step, setStep] = useState<Step>('upload');
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractionWarnings, setExtractionWarnings] = useState<string[]>([]);
  const [sanitizedPreview, setSanitizedPreview] = useState('');
  const [extractedMarkers, setExtractedMarkers] = useState<DetectedBiomarker[]>([]);
  const [userProfile, setUserProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [analysisResult, setAnalysisResult] = useState<FullAnalysisResponse | null>(null);

  const handleExtractionComplete = (data: ExtractionResponse) => {
    setSanitizedPreview(data.sanitized_preview);
    setExtractionWarnings(data.warnings || []);
    setExtractedMarkers(data.extracted_biomarkers);
    // Clean results go straight on; the review step only appears when something needs the person's attention.
    setStep(needsReview(data.extracted_biomarkers) ? 'verify' : 'profile');
  };

  const handleRunAnalysis = async (validatedProfile: UserProfile) => {
    setError(null);
    setIsAnalyzing(true);
    setIsLoading(true);
    try {
      const markerInputs: MarkerInput[] = extractedMarkers.map((m) => ({
        biomarker_key: m.biomarker_key,
        value: m.detected_value,
        unit: m.detected_unit,
        reference_low: m.report_reference_range?.low ?? null,
        reference_high: m.report_reference_range?.high ?? null,
      }));
      // Keep the multi-stage progress animation visible for a moment even on fast responses.
      const [res] = await Promise.all([
        analyzeAndRecommend(validatedProfile, markerInputs),
        new Promise((resolve) => setTimeout(resolve, 2500)),
      ]);
      setAnalysisResult(res);
      setStep('results');
    } catch (err) {
      setError((err as Error).message || 'Failed to complete nutritional analysis.');
    } finally {
      setIsAnalyzing(false);
      setIsLoading(false);
    }
  };

  const handleDownloadPdf = async (dietPlan?: FullAnalysisResponse['diet_plan']) => {
    if (!analysisResult) return;
    setIsExportingPdf(true);
    try {
      await downloadPlanPdf(dietPlan ? { ...analysisResult, diet_plan: dietPlan } : analysisResult);
    } catch (err) {
      setError('PDF generation failed: ' + (err as Error).message);
    } finally {
      setIsExportingPdf(false);
    }
  };

  const reset = useCallback(() => {
    setStep('upload');
    setExtractedMarkers([]);
    setExtractionWarnings([]);
    setSanitizedPreview('');
    setAnalysisResult(null);
    setError(null);
    setUserProfile(DEFAULT_PROFILE);
  }, []);

  return {
    step,
    setStep,
    isLoading,
    setIsLoading,
    isAnalyzing,
    isExportingPdf,
    error,
    extractionWarnings,
    sanitizedPreview,
    extractedMarkers,
    setExtractedMarkers,
    userProfile,
    setUserProfile,
    analysisResult,
    handleExtractionComplete,
    handleRunAnalysis,
    handleDownloadPdf,
    reset,
  };
}

export type Analyzer = ReturnType<typeof useAnalyzer>;
