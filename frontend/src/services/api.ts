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

export interface AssistantReply {
  reply: string;
  kind: 'answer' | 'clarify' | 'fallback' | 'safety' | 'refuse' | 'smalltalk';
  suggestions: string[];
  topic: string | null;
  conversation_id: string | null;
  saved: boolean;
}

export interface AssistantRequest {
  message: string;
  topic: string | null;
  context: unknown;
  conversation_id?: string | null;
  report_id?: string | null;
}

export async function askAssistant(request: AssistantRequest): Promise<AssistantReply> {
  return apiJson<AssistantReply>('/chat', {
    method: 'POST',
    json: request,
    signal: AbortSignal.timeout(30_000),
  });
}

export interface ChatSummary {
  id: string;
  title: string;
  report_id: string | null;
  report_date: string | null;
  preview: string;
  message_count: number;
  updated_at: string;
}

export interface ChatDetail {
  id: string;
  title: string;
  report_id: string | null;
  report_date: string | null;
  topic: string | null;
  updated_at: string;
  messages: { role: 'user' | 'bot'; text: string; kind: string; suggestions: string[]; created_at: string }[];
}

export const chatApi = {
  list: () => apiJson<ChatSummary[]>('/chat/conversations'),
  get: (id: string) => apiJson<ChatDetail>(`/chat/conversations/${encodeURIComponent(id)}`),
  remove: (id: string) => apiFetch(`/chat/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' }),
};
