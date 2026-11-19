import {
  ExtractionResponse, FullAnalysisResponse, MarkerInput, MealSlot, PlanDay, PlanStyle, ShoppingItem, UserProfile,
} from '../types';
import { apiFetch, apiJson } from './http';
import { currentLanguage } from '../lib/i18n';

/** Text of a photo or PDF of the person's usual diet (read with OCR on the server). */
export async function readDietFile(file: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);
  const r = await apiJson<{ text: string }>('/diet-text', { method: 'POST', body: formData, signal: AbortSignal.timeout(100_000) });
  return r.text;
}

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
  const response = await apiFetch(`/export-plan-pdf?lang=${currentLanguage()}`, { method: 'POST', json: analysisData });
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
  /** The website's language, so answers come in Hindi or Telugu when chosen. */
  language?: string;
  /** Guests' recent turns (signed-in chats are read from the server). */
  history?: { role: string; text: string }[];
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

/* ------------------------------------------------------------------ diet plans */

export interface PlanMarker {
  biomarker_key: string;
  status: string;
  target_nutrient_key: string | null;
}

export interface PlanInput {
  profile: UserProfile;
  markers: PlanMarker[];
  picked_foods: string[];
  style?: PlanStyle;
}

const PLAN_TIMEOUT = 120_000;

const planBody = (input: PlanInput) => ({
  profile: {
    age: input.profile.age,
    gender: input.profile.gender,
    height_cm: input.profile.height_cm,
    weight_kg: input.profile.weight_kg,
    activity: input.profile.activity ?? 'none',
    diet_type: input.profile.diet_type,
    meats: input.profile.meats ?? [],
    allergens: input.profile.allergens,
    custom_allergies: input.profile.custom_allergies ?? [],
    region: input.profile.region ?? '',
    existing_diet: input.profile.existing_diet ?? '',
  },
  markers: input.markers,
  picked_foods: input.picked_foods,
  style: input.style ?? 'familiar',
});

export async function planOptions(input: PlanInput): Promise<{ options: PlanDay[] }> {
  return apiJson('/diet-plan/options', { method: 'POST', json: planBody(input), signal: AbortSignal.timeout(PLAN_TIMEOUT) });
}

export async function planWeek(input: PlanInput): Promise<{ days: PlanDay[]; shopping_list: ShoppingItem[] }> {
  return apiJson('/diet-plan/week', { method: 'POST', json: planBody(input), signal: AbortSignal.timeout(PLAN_TIMEOUT) });
}

export async function planSwap(input: PlanInput, day: PlanDay, slot: MealSlot, dishId: string): Promise<{ day: PlanDay }> {
  return apiJson('/diet-plan/swap', {
    method: 'POST',
    json: { ...planBody(input), day, slot, dish_id: dishId },
    signal: AbortSignal.timeout(PLAN_TIMEOUT),
  });
}

export async function downloadDietPlanPdf(days: PlanDay[], shopping: ShoppingItem[]): Promise<void> {
  const response = await apiFetch(`/diet-plan/pdf?lang=${currentLanguage()}`, { method: 'POST', json: { days, shopping_list: shopping } });
  const url = window.URL.createObjectURL(await response.blob());
  const a = document.createElement('a');
  a.href = url;
  a.download = 'NutriLens_7_day_plan.pdf';
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function saveDietPlan(reportId: string, style: PlanStyle, days: PlanDay[], shopping: ShoppingItem[]): Promise<void> {
  await apiFetch(`/history/${reportId}/diet-plan`, { method: 'PUT', json: { style, days, shopping_list: shopping } });
}

/** The same results in Hindi or Telugu; results are stored in English. */
export async function localizeAnalysis(analysis: FullAnalysisResponse, lang: string): Promise<FullAnalysisResponse> {
  return apiJson<FullAnalysisResponse>(`/localize-analysis?lang=${lang}`, { method: 'POST', json: analysis });
}
