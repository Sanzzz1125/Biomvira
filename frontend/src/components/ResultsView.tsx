import React, { useState } from 'react';
import {
  Activity,
  Ban,
  CheckCircle2,
  Download,
  FileText,
  HeartPulse,
  RotateCcw,
  Leaf,
  Salad,
  Sparkles,
  Stethoscope,
  ThumbsUp,
} from 'lucide-react';
import { FullAnalysisResponse, UserProfile } from '../types';
import { RangeSliderBar } from './RangeSliderBar';
import { FoodCard } from './FoodCard';
import { ClinicalNarrative } from './ClinicalNarrative';
import { Alert, Badge, Button, Card, SectionTitle, STATUS_META, cx } from './ui';

interface ResultsViewProps {
  result: FullAnalysisResponse;
  profile: UserProfile;
  isExporting: boolean;
  onDownload: () => void;
  onReset: () => void;
  resetLabel?: string;
  resetIcon?: React.ReactNode;
}

const SUMMARY_CARDS = [
  { key: 'low', label: 'Low', hint: 'Needs attention', status: 'low' },
  { key: 'borderline', label: 'Borderline', hint: 'Worth monitoring', status: 'borderline' },
  { key: 'normal', label: 'Optimal', hint: 'In healthy range', status: 'normal' },
  { key: 'high', label: 'Elevated', hint: 'Above healthy range', status: 'high' },
] as const;

export const ResultsView: React.FC<ResultsViewProps> = ({
  result,
  profile,
  isExporting,
  onDownload,
  onReset,
  resetLabel = 'New analysis',
  resetIcon = <RotateCcw className="h-4 w-4" aria-hidden />,
}) => {
  const [markerFilter, setMarkerFilter] = useState<'all' | 'flagged'>('all');

  const totalMarkers = result.marker_analyses.length || 1;
  const optimalCount = result.status_summary['normal'] || 0;
  const lowCount = result.status_summary['low'] || 0;
  const borderlineCount = result.status_summary['borderline'] || 0;
  const elevatedCount = result.status_summary['high'] || 0;

  const optimalPercent = Math.round((optimalCount / totalMarkers) * 100);

  const flaggedCount = result.marker_analyses.filter((m) => m.status !== 'normal').length;
  const visibleMarkers = result.marker_analyses.filter(
    (m) => markerFilter === 'all' || m.status !== 'normal'
  );

  const filters = [
    { id: 'all' as const, label: `All (${result.marker_analyses.length})` },
    { id: 'flagged' as const, label: `Needs attention (${flaggedCount})` },
  ];

  // Plans saved before "maintain" plans existed have no purpose and are improvement plans.
  const improvePlans = result.recommendations.filter((p) => (p.purpose ?? 'improve') === 'improve');
  const maintainPlans = result.recommendations.filter((p) => p.purpose === 'maintain');

  return (
    <div className="mx-auto max-w-6xl space-y-10 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="brand" icon={<CheckCircle2 className="h-3.5 w-3.5" aria-hidden />}>
              Analysis complete
            </Badge>
            <span className="text-xs text-slate-500 font-mono tabular-nums">
              Ref #{result.analysis_id.slice(0, 8)}
            </span>
          </div>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
            Personalized Clinical Nutrition Plan
          </h2>
          <p className="mt-2 text-[15px] text-slate-600">
            Formulated for a{' '}
            <span className="font-semibold capitalize text-slate-900">
              {profile.diet_type.replace('_', ' ')}
            </span>{' '}
            diet
            {profile.allergens.length > 0 ? (
              <>
                , strictly excluding{' '}
                <span className="font-semibold text-slate-900">
                  {profile.allergens.join(', ')}
                </span>.
              </>
            ) : (
              <>, with zero dietary exclusions.</>
            )}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="secondary"
            onClick={onReset}
            icon={resetIcon}
          >
            {resetLabel}
          </Button>
          <Button
            onClick={onDownload}
            loading={isExporting}
            icon={<Download className="h-4 w-4" aria-hidden />}
          >
            {isExporting ? 'Preparing PDF…' : 'Download PDF'}
          </Button>
        </div>
      </div>

      {/* Biomarker Index Bar */}
      <Card className="overflow-hidden p-6 bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-[11px] font-mono tracking-wider uppercase text-emerald-400 font-semibold block">
              Biomarker Homeostasis Score
            </span>
            <h3 className="text-2xl font-bold text-white tracking-tight mt-0.5">
              {optimalCount} of {result.marker_analyses.length} Biomarkers in Target Range
            </h3>
            <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
              {flaggedCount === 0
                ? 'All tested laboratory biomarkers are balanced within reference intervals.'
                : `${flaggedCount} biomarker${flaggedCount > 1 ? 's require' : ' requires'} attention; food guidance is given where it applies, and anything urgent is marked clearly.`}
            </p>
          </div>

          <div className="flex items-center gap-4 self-start md:self-auto shrink-0">
            <div className="text-right">
              <span className="text-3xl font-mono font-bold text-emerald-400 tabular-nums">
                {optimalPercent}%
              </span>
              <p className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
                Optimal Index
              </p>
            </div>
          </div>
        </div>

        {/* Visual Multi-Segment Bar */}
        <div className="mt-5 h-2.5 w-full overflow-hidden rounded-full bg-slate-700/60 flex">
          <div
            style={{ width: `${(optimalCount / totalMarkers) * 100}%` }}
            className="bg-emerald-500 h-full transition-all duration-500"
            title={`${optimalCount} Optimal`}
          />
          <div
            style={{ width: `${(borderlineCount / totalMarkers) * 100}%` }}
            className="bg-amber-500 h-full transition-all duration-500"
            title={`${borderlineCount} Borderline`}
          />
          <div
            style={{ width: `${(lowCount / totalMarkers) * 100}%` }}
            className="bg-red-500 h-full transition-all duration-500"
            title={`${lowCount} Low`}
          />
          <div
            style={{ width: `${(elevatedCount / totalMarkers) * 100}%` }}
            className="bg-indigo-500 h-full transition-all duration-500"
            title={`${elevatedCount} Elevated`}
          />
        </div>
      </Card>

      {/* Summary Stat Cards */}
      <section aria-label="Summary" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {SUMMARY_CARDS.map(({ key, label, hint, status }) => {
          const meta = STATUS_META[status];
          return (
            <Card key={key} className="relative overflow-hidden p-5 shadow-card hover:shadow-card-lg transition-shadow">
              <span className={cx('absolute inset-x-0 top-0 h-1', meta.bar)} aria-hidden />
              <p className="text-sm font-medium text-slate-600">{label}</p>
              <p className="mt-2 text-4xl font-bold tracking-tight text-slate-900 tabular-nums">
                {result.status_summary[key] || 0}
              </p>
              <p className="mt-1 text-xs text-slate-500">{hint}</p>
            </Card>
          );
        })}
      </section>

      {/* Critical Physician advisory */}
      {result.requires_physician_consult && (
        <Alert
          tone="error"
          icon={<HeartPulse className="h-5 w-5 text-red-600" aria-hidden />}
          title="Clinical Safety Warning — Doctor Consultation Required"
          className="p-5"
        >
          <p className="text-sm text-red-900 font-medium leading-relaxed">
            One or more results need a doctor’s attention; food-first nutrition alone is not enough. Please consult a licensed physician:
          </p>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-xs text-red-800 marker:text-red-500">
            {result.consult_reasons.map((reason, idx) => (
              <li key={idx} className="leading-relaxed font-semibold">{reason}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Biomarkers Overview */}
      <section aria-labelledby="biomarkers-heading" className="space-y-5">
        <SectionTitle
          icon={<Activity className="h-[18px] w-[18px]" aria-hidden />}
          title="Laboratory Biomarker Evaluations"
          description="Your values calibrated against printed laboratory reference intervals and clinical guidelines."
          right={
            <div role="tablist" aria-label="Filter biomarkers" className="inline-flex self-start rounded-lg bg-slate-100 p-1">
              {filters.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  role="tab"
                  aria-selected={markerFilter === f.id}
                  onClick={() => setMarkerFilter(f.id)}
                  className={cx(
                    'rounded-md px-3 py-1.5 text-sm font-medium transition-all',
                    markerFilter === f.id
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          }
        />
        <span id="biomarkers-heading" className="sr-only">
          Biomarker overview
        </span>

        {visibleMarkers.length === 0 ? (
          <Card className="px-6 py-10 text-center text-sm text-slate-500">
            No biomarkers match the filter. All values are in the optimal biological range.
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {visibleMarkers.map((marker) => (
              <RangeSliderBar key={marker.biomarker_key} analysis={marker} />
            ))}
          </div>
        )}
      </section>

      {/* Food plans */}
      <section className="space-y-5">
        <SectionTitle
          icon={<Salad className="h-[18px] w-[18px]" aria-hidden />}
          title="Targeted Nutrition Protocols"
          description="Foods are chosen for the nutrient or property that matters for each result, with strict diet and allergen safety."
        />

        {improvePlans.length === 0 ? (
          <Card className="px-6 py-12 text-center">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
              <CheckCircle2 className="h-6 w-6" aria-hidden />
            </span>
            <h4 className="mt-4 text-[15px] font-semibold text-slate-900">
              Biochemical Parameters Balanced
            </h4>
            <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
              None of your results needs a corrective food plan. See the foods below to keep your healthy results where they are.
            </p>
          </Card>
        ) : (
          <div className="space-y-6">
            {improvePlans.map((plan) => {
              const meta = STATUS_META[plan.status];
              return (
                <Card key={plan.target_biomarker} className="overflow-hidden shadow-card">
                  <div className="flex flex-col gap-2 border-b border-slate-200 bg-slate-50 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="eyebrow">Target Goal</p>
                      <h4 className="mt-0.5 text-lg font-semibold text-slate-900">
                        Nutritional Protocol for {plan.biomarker_display_name}
                      </h4>
                    </div>
                    <Badge tone={meta.tone} className="self-start sm:self-auto">
                      <span className={cx('h-1.5 w-1.5 rounded-full', meta.dot)} aria-hidden />
                      {meta.label} Status
                    </Badge>
                  </div>

                  <div className="space-y-6 p-6">
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                      {plan.recommended_foods.map((food) => (
                        <FoodCard
                          key={food.id}
                          food={food}
                          targetNutrientName={plan.biomarker_display_name}
                        />
                      ))}
                    </div>

                    <div className="grid gap-4 md:grid-cols-2 pt-2 border-t border-slate-100">
                      <div className="rounded-xl border border-brand-200 bg-brand-50/60 p-5">
                        <h5 className="flex items-center gap-2 text-sm font-semibold text-brand-800">
                          <ThumbsUp className="h-4 w-4" aria-hidden />
                          Helpful Habits and Absorption Tips
                        </h5>
                        <ul className="mt-3 space-y-2 text-xs leading-relaxed text-slate-700">
                          {plan.absorption_dos.map((tip, i) => (
                            <li key={i} className="flex items-start gap-2.5">
                              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" aria-hidden />
                              <span>{tip}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="rounded-xl border border-red-200 bg-red-50/60 p-5">
                        <h5 className="flex items-center gap-2 text-sm font-semibold text-red-800">
                          <Ban className="h-4 w-4" aria-hidden />
                          Habits to Limit or Avoid
                        </h5>
                        <ul className="mt-3 space-y-2 text-xs leading-relaxed text-slate-700">
                          {plan.absorption_donts.map((tip, i) => (
                            <li key={i} className="flex items-start gap-2.5">
                              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" aria-hidden />
                              <span>{tip}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {maintainPlans.length > 0 && (
        <section className="space-y-5">
          <SectionTitle
            icon={<Leaf className="h-[18px] w-[18px]" aria-hidden />}
            title="Keep Your Healthy Results Healthy"
            description="These results are within range. Including these foods regularly helps keep them there."
          />
          <div className="grid gap-5 lg:grid-cols-2">
            {maintainPlans.map((plan) => (
              <Card key={plan.target_biomarker} className="overflow-hidden">
                <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-3.5">
                  <h4 className="text-[15px] font-semibold text-slate-900">{plan.biomarker_display_name}</h4>
                  <Badge tone="brand" className="shrink-0">
                    <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
                    Within range
                  </Badge>
                </div>
                <div className="space-y-4 p-5">
                  <ul className="grid gap-2.5 sm:grid-cols-2">
                    {plan.recommended_foods.map((food) => (
                      <li key={food.id} className="rounded-lg border border-slate-200 bg-slate-50/60 px-3.5 py-2.5">
                        <p className="text-sm font-semibold text-slate-900">{food.name}</p>
                        <p className="mt-0.5 text-xs text-slate-500">
                          {/\d/.test(food.key_nutrient_yield)
                            ? `${food.key_nutrient_yield} per ${food.serving_size}`
                            : `${food.key_nutrient_yield} · ${food.serving_size}`}
                        </p>
                      </li>
                    ))}
                  </ul>
                  {plan.absorption_dos[0] && (
                    <p className="flex items-start gap-2 text-xs leading-relaxed text-slate-600">
                      <ThumbsUp className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-600" aria-hidden />
                      {plan.absorption_dos[0]}
                    </p>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Clinical Synthesis & Narrative */}
      <section>
        <ClinicalNarrative result={result} />
      </section>
    </div>
  );
};
