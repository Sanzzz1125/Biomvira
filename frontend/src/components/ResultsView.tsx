import { hasKey, StringKey, useLanguage, useT } from '../lib/i18n';
import { translateText } from '../lib/domTranslate';
import React, { useEffect, useRef, useState } from 'react';
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
  Utensils,
} from 'lucide-react';
import { FullAnalysisResponse, UserProfile } from '../types';
import { RangeSliderBar } from './RangeSliderBar';
import { FoodCard } from './FoodCard';
import { PlanBuilder, WeekPlan } from './PlanBuilder';
import { useLocalizedResult } from '../hooks/useLocalizedResult';
import { ClinicalNarrative } from './ClinicalNarrative';
import { Alert, Badge, Button, Card, SectionTitle, STATUS_META, cx } from './ui';
import { chatContextFromAnalysis, setChatContext } from '../lib/chatContext';

interface ResultsViewProps {
  result: FullAnalysisResponse;
  profile: UserProfile;
  isExporting: boolean;
  /** Downloads the report PDF; the 7-day plan on screen (if any) is included in it. */
  onDownload: (dietPlan?: WeekPlan | null) => void;
  onReset: () => void;
  resetLabel?: string;
  resetIcon?: React.ReactNode;
  /** The saved report these results belong to (signed-in users), so assistant chats can be linked to it. */
  savedReportId?: string | null;
}

const SUMMARY_CARDS = [
  { key: 'low', label: 'Low', hint: 'Needs attention', status: 'low' },
  { key: 'borderline', label: 'Borderline', hint: 'Worth monitoring', status: 'borderline' },
  { key: 'normal', label: 'Optimal', hint: 'In healthy range', status: 'normal' },
  { key: 'high', label: 'Elevated', hint: 'Above healthy range', status: 'high' },
] as const;

export const ResultsView: React.FC<ResultsViewProps> = ({
  result: source,
  profile,
  isExporting,
  onDownload,
  onReset,
  resetLabel = 'New analysis',
  resetIcon = <RotateCcw className="h-4 w-4" aria-hidden />,
  savedReportId = null,
}) => {
  const result = useLocalizedResult(source);
  const t = useT();
  const language = useLanguage();
  const [markerFilter, setMarkerFilter] = useState<'all' | 'flagged'>('all');
  const [picked, setPicked] = useState<string[]>([]);
  const togglePick = (id: string) =>
    setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id].slice(0, 30)));
  // Picks reach the diet plan when the person asks for it ("Update my diet plan"), not on every tap.
  const [appliedPicks, setAppliedPicks] = useState<string[]>([]);
  const [rebuildToken, setRebuildToken] = useState(0);
  const picksChanged = [...picked].sort().join() !== [...appliedPicks].sort().join();
  const [week, setWeek] = useState<WeekPlan | null>(null);
  // Foods come first (pick what you like, then build the plan); a saved plan opens on the plan itself.
  const [activeTab, setActiveTab] = useState<'plan' | 'tests' | 'foods'>(source.diet_plan ? 'plan' : 'foods');
  // The plan builder starts (and builds its options) the first time its tab is opened, with the picks made by then.
  const [planOpened, setPlanOpened] = useState(!!source.diet_plan);
  const tabsRef = useRef<HTMLDivElement>(null);
  // A new tab starts at its top: scroll back to where the tab bar sits when the page has scrolled past it.
  const openTab = (id: 'plan' | 'tests' | 'foods') => {
    setActiveTab(id);
    if (id === 'plan') setPlanOpened(true);
    const top = tabsRef.current?.getBoundingClientRect().top;
    if (top !== undefined && top < 0) window.scrollTo?.({ top: window.scrollY + top - 92, behavior: 'smooth' });
  };
  const applyPicks = () => {
    setAppliedPicks(picked);
    if (planOpened && picksChanged) setRebuildToken((n) => n + 1);
    openTab('plan');
  };

  // Let the assistant answer questions about these results while they are on screen.
  useEffect(() => {
    setChatContext(chatContextFromAnalysis(week ? { ...source, diet_plan: week } : source, savedReportId));
    return () => setChatContext(null);
  }, [source, savedReportId, week]);

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
    { id: 'all' as const, label: t('allCount', { n: result.marker_analyses.length }) },
    { id: 'flagged' as const, label: t('needsAttentionCount', { n: flaggedCount }) },
  ];

  const tabs = [
    { id: 'foods' as const, label: t('tabStepFoods'), icon: <Salad className="h-4 w-4" aria-hidden /> },
    { id: 'plan' as const, label: t('tabStepPlan'), icon: <Utensils className="h-4 w-4" aria-hidden /> },
    { id: 'tests' as const, label: t('tabTests', { n: result.marker_analyses.length }), icon: <Activity className="h-4 w-4" aria-hidden /> },
  ];

  // Plans saved before "maintain" plans existed have no purpose and are improvement plans.
  const improvePlans = result.recommendations.filter((p) => (p.purpose ?? 'improve') === 'improve');
  const maintainPlans = result.recommendations.filter((p) => p.purpose === 'maintain');

  return (
    <div className="space-y-8 animate-fade-in">
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
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{t('resultsTitle')}</h2>
          <p className="mt-2 text-[15px] text-slate-600" translate="no">
            {(() => {
              const diet = language === 'en' ? profile.diet_type.replace('_', ' ') : t(`diet_${profile.diet_type}` as StringKey);
              const [before, after] = t('formulated', { diet: '\u0000' }).split('\u0000');
              const list = profile.allergens.map((a) => (hasKey(`allergen_${a}`) ? t(`allergen_${a}` as StringKey) : a)).join(', ');
              const [exBefore, exAfter] = t('excluding', { list: '\u0000' }).split('\u0000');
              return (
                <>
                  {before}<span className="font-semibold capitalize text-slate-900">{diet}</span>{after}
                  {profile.allergens.length > 0 ? (
                    <>{exBefore}<span className="font-semibold text-slate-900">{list}</span>{exAfter}</>
                  ) : t('noExclusions')}
                </>
              );
            })()}
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
            onClick={() => onDownload(week)}
            loading={isExporting}
            icon={<Download className="h-4 w-4" aria-hidden />}
          >
            {isExporting ? 'Preparing PDF…' : 'Download PDF'}
          </Button>
        </div>
      </div>

      {/* Health score: a light card in the site's colours (the PDF uses the same design) */}
      <Card className="overflow-hidden p-5 shadow-card sm:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-center gap-5">
            <div className="relative h-20 w-20 shrink-0" aria-hidden>
              <svg viewBox="0 0 36 36" className="h-20 w-20 -rotate-90">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#e2e8f0" strokeWidth="3.5" />
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#167c64" strokeWidth="3.5" strokeLinecap="round"
                  strokeDasharray={`${(optimalCount / totalMarkers) * 97.4} 97.4`} />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-lg font-bold tabular-nums text-slate-900">
                {optimalPercent}%
              </span>
            </div>
            <div className="min-w-0">
              <p className="eyebrow">Health score</p>
              <h3 className="mt-0.5 text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
                {t('inHealthyRange', { a: optimalCount, n: result.marker_analyses.length })}
              </h3>
              <p className="mt-1 max-w-xl text-sm leading-relaxed text-slate-600">
                {flaggedCount === 0
                  ? 'All your results are within healthy ranges.'
                  : t(flaggedCount > 1 ? 'needManySentence' : 'needOneSentence', { n: flaggedCount })}
              </p>
            </div>
          </div>
          <ul aria-label="Summary" className="grid shrink-0 grid-cols-4 gap-2">
            {SUMMARY_CARDS.map(({ key, label, status }) => (
              <li key={key} className="min-w-[72px] rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-center">
                <p className="text-2xl font-bold tabular-nums text-slate-900">{result.status_summary[key] || 0}</p>
                <p className="mt-0.5 flex items-center justify-center gap-1 text-[11px] font-medium text-slate-600">
                  <span className={cx('h-1.5 w-1.5 rounded-full', STATUS_META[status].dot)} aria-hidden />
                  {label}
                </p>
              </li>
            ))}
          </ul>
        </div>
        <div className="mt-5 flex h-2 w-full overflow-hidden rounded-full bg-slate-100" aria-hidden>
          <div style={{ width: `${(optimalCount / totalMarkers) * 100}%` }} className="h-full bg-emerald-500" />
          <div style={{ width: `${(borderlineCount / totalMarkers) * 100}%` }} className="h-full bg-amber-500" />
          <div style={{ width: `${(lowCount / totalMarkers) * 100}%` }} className="h-full bg-red-500" />
          <div style={{ width: `${(elevatedCount / totalMarkers) * 100}%` }} className="h-full bg-indigo-500" />
        </div>
      </Card>

      {/* Critical Physician advisory */}
      {result.requires_physician_consult && (
        <Alert
          tone="error"
          icon={<HeartPulse className="h-5 w-5 text-red-600" aria-hidden />}
          title="Please review these results with a doctor"
          className="p-5"
        >
          <p className="text-sm text-red-900 font-medium leading-relaxed">
            Food changes can support your health, but the following results need medical advice:
          </p>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-xs text-red-800 marker:text-red-500">
            {result.consult_reasons.map((reason, idx) => (
              <li key={idx} className="leading-relaxed font-semibold">{reason}</li>
            ))}
          </ul>
        </Alert>
      )}

      {!!result.allergy_conflicts?.length && (
        <Alert tone="warning" title={t('conflictTitle')}>
          <p>{t('conflictText')}</p>
          <ul className="mt-2 list-disc space-y-0.5 pl-5">
            {result.allergy_conflicts.map((name) => <li key={name}>{name}</li>)}
          </ul>
          <Button size="sm" variant="secondary" className="mt-3"
            onClick={() => { setRebuildToken((n) => n + 1); openTab('plan'); }}>
            {t('conflictRebuild')}
          </Button>
        </Alert>
      )}

      {/* The diet plan is the main result; test details and foods are one tap away. */}
      <div ref={tabsRef} aria-hidden className="-mb-8 h-0" />
      <div className="sticky top-[76px] z-20 -mx-4 scroll-mt-16 border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:mx-0 sm:rounded-2xl sm:border sm:px-2">
        <div role="tablist" aria-label={t('resultTabs')} className="flex gap-1 overflow-x-auto py-2">
          {tabs.map((tab) => (
            <button key={tab.id} type="button" role="tab" id={`tab-${tab.id}`} aria-controls={`panel-${tab.id}`}
              aria-selected={activeTab === tab.id} onClick={() => openTab(tab.id)}
              className={cx('inline-flex h-11 shrink-0 items-center gap-2 rounded-xl px-4 text-sm font-semibold transition-colors',
                activeTab === tab.id ? 'bg-brand-600 text-white' : 'text-slate-700 hover:bg-slate-100')}>
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <section id="diet-plan" role="tabpanel" aria-labelledby="tab-plan" hidden={activeTab !== 'plan'}>
        {planOpened && (
          <PlanBuilder result={source} profile={profile} picked={appliedPicks} reportId={savedReportId}
            rebuildToken={rebuildToken} onWeekChange={setWeek} onChooseFoods={() => openTab('foods')} />
        )}
      </section>

      <div id="panel-tests" role="tabpanel" aria-labelledby="tab-tests" hidden={activeTab !== 'tests'} className="space-y-10">
      {/* Biomarkers Overview */}
      <section aria-labelledby="biomarkers-heading" className="space-y-5">
        <SectionTitle
          icon={<Activity className="h-[18px] w-[18px]" aria-hidden />}
          title="Your Test Results"
          description="Each result compared with your lab's reference range or clinical guidelines."
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
            No results need attention. All values are within the healthy range.
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {visibleMarkers.map((marker) => (
              <RangeSliderBar key={marker.biomarker_key} analysis={marker} />
            ))}
          </div>
        )}
      </section>

        <section>
          <ClinicalNarrative result={result} />
        </section>
      </div>

      <div id="panel-foods" role="tabpanel" aria-labelledby="tab-foods" hidden={activeTab !== 'foods'} className="space-y-10">
        <p className="rounded-xl border border-brand-200 bg-brand-50/60 px-4 py-3 text-sm text-brand-800">{t('foodsIntro')}</p>
      {/* Food plans */}
      <section className="space-y-5">
        <SectionTitle
          icon={<Salad className="h-[18px] w-[18px]" aria-hidden />}
          title="Your Food Plan"
          description="Indian foods chosen for each result that needs attention, matched to your diet and allergies."
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
                      <p className="eyebrow">Food plan</p>
                      <h4 className="mt-0.5 text-lg font-semibold text-slate-900">
                        {t('forName', { name: plan.biomarker_display_name })}
                      </h4>
                    </div>
                    <Badge tone={meta.tone} className="self-start sm:self-auto">
                      <span className={cx('h-1.5 w-1.5 rounded-full', meta.dot)} aria-hidden />
                      {t('statusLabel', { label: translateText(meta.label) })}
                    </Badge>
                  </div>

                  <div className="space-y-6 p-4 sm:p-6">
                    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                      {plan.recommended_foods.map((food) => (
                        <FoodCard
                          key={food.id}
                          food={food}
                          targetNutrientName={plan.biomarker_display_name}
                          selected={picked.includes(food.id)}
                          onToggle={() => togglePick(food.id)}
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

      </div>

      {activeTab === 'foods' && (
        <div className="sticky bottom-24 z-20 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl border border-brand-200 bg-white px-4 py-3 shadow-card-lg sm:w-fit sm:max-w-[calc(100%-340px)]">
          <Button onClick={applyPicks} icon={<Sparkles className="h-4 w-4" aria-hidden />}>
            {!planOpened ? t('buildPlanNow') : picksChanged ? t('updatePlan') : t('seePlan')}
          </Button>
          <span className="text-sm font-medium text-slate-800">
            {picked.length === 1 ? t('foodsPickedOne') : picked.length > 1 ? t('foodsPickedBar', { n: picked.length }) : t('noPicksYet')}
          </span>
        </div>
      )}
    </div>
  );
};
