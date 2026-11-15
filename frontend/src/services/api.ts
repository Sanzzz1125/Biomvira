import { ExtractionResponse, FullAnalysisResponse, MarkerInput, UserProfile } from '../types';
import { apiFetch, apiJson } from './http';

export async function extractReport(file?: File, rawText?: string): Promise<ExtractionResponse> {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  } else if (rawText) {
    formData.append('raw_text', rawText);
  } else {
    throw new Error('Please provide either a file or report text');
  }
  return apiJson<ExtractionResponse>('/extract-report', {
    method: 'POST',
    body: formData,
    signal: AbortSignal.timeout(100_000),
  });
}

export async function analyzeAndRecommend(
  userProfile: UserProfile,
  biomarkers: MarkerInput[]
): Promise<FullAnalysisResponse> {
  return apiJson<FullAnalysisResponse>('/analyze-and-recommend', {
    method: 'POST',
    json: { user_profile: userProfile, biomarkers },
  });
}

export async function downloadPlanPdf(analysisData: FullAnalysisResponse): Promise<void> {
  const response = await apiFetch('/export-plan-pdf', { method: 'POST', json: analysisData });
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `NutriLens_Nutrition_Plan_${analysisData.analysis_id.slice(0, 8)}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
