import { useSyncExternalStore } from 'react';
import { FullAnalysisResponse } from '../types';

/** The results the assistant may use for personal answers. Only kept in memory while a results page is open. */
export interface ChatContext {
  markers: {
    key: string;
    name: string;
    value: number;
    unit: string;
    status: string;
    range_low: number | null;
    range_high: number | null;
  }[];
  plans: { name: string; purpose: string; foods: string[] }[];
  diet_type: string;
  allergens: string[];
  /** Allergies the person typed in ("peanut", "brinjal") and, for non-vegetarians, the meats they eat. */
  custom_allergies: string[];
  meats: string[];
  /** The 7-day plan on screen (or saved with the report): dish names per meal for each day. */
  diet_plan: { style: string; days: { kcal: number; meals: Record<string, string[]> }[] } | null;
  /** Set when the results belong to a saved report, so a signed-in user's chat can be linked to it. */
  reportId: string | null;
  reportDate: string;
  needAttention: number;
}

let current: ChatContext | null = null;
const listeners = new Set<() => void>();

export function chatContextFromAnalysis(result: FullAnalysisResponse, reportId?: string | null): ChatContext {
  return {
    reportId: reportId ?? null,
    reportDate: result.timestamp,
    needAttention: result.marker_analyses.filter((m) => m.status !== 'normal').length,
    markers: result.marker_analyses.map((m) => ({
      key: m.biomarker_key,
      name: m.display_name,
      value: m.value,
      unit: m.unit,
      status: m.status,
      range_low: Number.isFinite(m.range_low) ? m.range_low : null,
      range_high: Number.isFinite(m.range_high) ? m.range_high : null,
    })),
    plans: result.recommendations.map((p) => ({
      name: p.biomarker_display_name,
      purpose: p.purpose ?? 'improve',
      foods: p.recommended_foods.map((f) => f.name),
    })),
    diet_type: result.user_profile.diet_type,
    allergens: result.user_profile.allergens,
    custom_allergies: result.user_profile.custom_allergies ?? [],
    meats: result.user_profile.meats ?? [],
    diet_plan: result.diet_plan?.days?.length
      ? {
          style: result.diet_plan.style,
          days: result.diet_plan.days.slice(0, 7).map((d) => ({
            kcal: Math.round(d.totals.energy_kcal),
            meals: Object.fromEntries(Object.entries(d.meals).map(([slot, items]) => [slot, items.map((i) => i.name)])),
          })),
        }
      : null,
  };
}

export function setChatContext(context: ChatContext | null): void {
  current = context;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useChatContext(): ChatContext | null {
  return useSyncExternalStore(subscribe, () => current, () => null);
}

/** The part of the context the assistant API understands. */
export function contextPayload(context: ChatContext | null) {
  if (!context) return null;
  const { markers, plans, diet_type, allergens, custom_allergies, meats, diet_plan } = context;
  return { markers, plans, diet_type, allergens, custom_allergies, meats, diet_plan };
}
