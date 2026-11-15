import React from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  ChevronRight,
  Clock,
  Dna,
  FileText,
  HeartPulse,
  Info,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  ThumbsDown,
  ThumbsUp,
  Utensils,
} from 'lucide-react';
import { FullAnalysisResponse } from '../types';
import { Badge, Card, cx } from './ui';

interface ClinicalNarrativeProps {
  result: FullAnalysisResponse;
}

export const ClinicalNarrative: React.FC<ClinicalNarrativeProps> = ({ result }) => {
  const explanation = result.grounded_explanation || '';
  const flaggedMarkers = result.marker_analyses.filter((m) => m.status !== 'normal');
  const optimalMarkers = result.marker_analyses.filter((m) => m.status === 'normal');

  // Helper to parse simple markdown formatting (bold, italic)
  const formatText = (text: string) => {
    // Split by bold (**text**)
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} className="font-semibold text-slate-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      // Check for italic (*text*)
      const subParts = part.split(/(\*.*?\*)/g);
      return subParts.map((sub, j) => {
        if (sub.startsWith('*') && sub.endsWith('*')) {
          return (
            <em key={`${i}-${j}`} className="italic text-slate-700">
              {sub.slice(1, -1)}
            </em>
          );
        }
        return sub;
      });
    });
  };

  // Extract sections from markdown text
  const sections = explanation.split(/^###?\s+/m).filter(Boolean);

  return (
    <div className="space-y-6">
      {/* Executive Clinical Assessment Card */}
      <Card className="overflow-hidden border-brand-200/80 shadow-card">
        <div className="border-b border-brand-100 bg-gradient-to-r from-brand-50/80 via-brand-50/30 to-white px-6 py-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm ring-4 ring-brand-100">
                <Stethoscope className="h-5 w-5" />
              </span>
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Clinical Synthesis & Metabolic Interpretation
                </h3>
                <p className="text-xs text-slate-500">
                  Physiological evaluation grounded in ICMR-NIN nutritional composition
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge tone={flaggedMarkers.length === 0 ? 'brand' : 'amber'}>
                {flaggedMarkers.length === 0
                  ? 'All Biomarkers Optimal'
                  : `${flaggedMarkers.length} Parameter${flaggedMarkers.length > 1 ? 's' : ''} Flagged`}
              </Badge>
              <Badge tone="neutral">
                {Math.round((optimalMarkers.length / (result.marker_analyses.length || 1)) * 100)}% Optimal Index
              </Badge>
            </div>
          </div>
        </div>

        <div className="p-6 sm:p-8 space-y-6">
          {/* Overview Paragraph */}
          <div className="rounded-xl border border-slate-200/70 bg-slate-50/70 p-5 text-[15px] leading-relaxed text-slate-700">
            {flaggedMarkers.length === 0 ? (
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 shrink-0 text-brand-600 mt-0.5" />
                <p>
                  All <strong>{result.marker_analyses.length} tested biomarkers</strong> reside comfortably within standard biological reference intervals. Your blood chemistry indicates robust physiological homeostasis across oxygen transport, bone mineralization, and neuro-cellular cellular stores.
                </p>
              </div>
            ) : (
              <p>
                Laboratory analysis reveals that <strong>{flaggedMarkers.length} of {result.marker_analyses.length} parameters</strong> are below reference intervals ({flaggedMarkers.filter(m => m.status === 'low').length} Low, {flaggedMarkers.filter(m => m.status === 'borderline').length} Borderline). The therapeutic food protocol below focuses on nutrient-dense Indian staples with high absorption bioavailability to support restoration.
              </p>
            )}
          </div>

          {/* Biomarker Depletion Breakdown */}
          {flaggedMarkers.length > 0 && (
            <div className="space-y-4">
              <h4 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-800">
                <Activity className="h-4 w-4 text-brand-600" />
                Biomarker Depletion & Physiological Impact
              </h4>
              <div className="grid gap-4 md:grid-cols-2">
                {flaggedMarkers.map((m) => (
                  <div
                    key={m.biomarker_key}
                    className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-slate-300"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h5 className="font-semibold text-slate-900">{m.display_name}</h5>
                          <p className="font-mono text-xs text-slate-500 mt-0.5">
                            Reported: <span className="font-bold text-slate-800">{m.value} {m.unit}</span> (Ref: {m.range_low} – {m.range_high} {m.unit})
                          </p>
                        </div>
                        <span
                          className={cx(
                            'rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize',
                            m.status === 'low'
                              ? 'bg-red-50 text-red-700 ring-1 ring-red-200'
                              : 'bg-amber-50 text-amber-800 ring-1 ring-amber-200'
                          )}
                        >
                          {m.status} ({Math.round(m.percentage_of_optimal)}% optimal)
                        </span>
                      </div>

                      <p className="mt-3 text-xs leading-relaxed text-slate-600">
                        {m.clinical_warning ||
                          (m.status === 'low'
                            ? `Value is significantly below the laboratory's reference range (${m.range_low} ${m.unit}). Cellular stores require targeted nutritional repletion.`
                            : `Value is on the borderline threshold. Preventative nutritional intervention recommended to avoid depletion.`)}
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-medium">
                      <span>Primary Target</span>
                      <span className="text-brand-700 font-semibold capitalize">{m.target_nutrient_key.replace('_', ' ')}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actionable Absorption Synergies & Inhibitors */}
          {result.recommendations.length > 0 && (
            <div className="space-y-4">
              <h4 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-800">
                <Dna className="h-4 w-4 text-brand-600" />
                Absorption Kinetics & Bioavailability Rules
              </h4>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
                  <div className="flex items-center gap-2 text-sm font-semibold text-emerald-800">
                    <ThumbsUp className="h-4 w-4 text-emerald-600" />
                    Bioavailability Synergies (Catalysts)
                  </div>
                  <ul className="mt-3 space-y-2.5 text-xs text-slate-700 leading-relaxed">
                    {result.recommendations.flatMap((r) => r.absorption_dos).slice(0, 3).map((tip, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600" />
                        <span>{formatText(tip)}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-5">
                  <div className="flex items-center gap-2 text-sm font-semibold text-rose-800">
                    <ThumbsDown className="h-4 w-4 text-rose-600" />
                    Absorption Antagonists (Inhibitors to Space)
                  </div>
                  <ul className="mt-3 space-y-2.5 text-xs text-slate-700 leading-relaxed">
                    {result.recommendations.flatMap((r) => r.absorption_donts).slice(0, 3).map((tip, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-600" />
                        <span>{formatText(tip)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Critical Clinical Alert if Required */}
          {result.requires_physician_consult && (
            <div className="rounded-xl border border-red-200 bg-red-50/80 p-5 text-red-900 shadow-sm">
              <div className="flex items-start gap-3">
                <ShieldAlert className="h-5 w-5 shrink-0 text-red-600 mt-0.5" />
                <div>
                  <h5 className="text-sm font-bold text-red-900">
                    Clinical Supervision Recommended
                  </h5>
                  <p className="mt-1 text-xs leading-relaxed text-red-800">
                    One or more of your biomarkers have crossed critical depletion limits (e.g. severe anemia or acute deficiency). Dietary changes should complement, not replace, medical evaluation.
                  </p>
                  <ul className="mt-2 list-disc list-inside text-xs text-red-700 space-y-1">
                    {result.consult_reasons.map((reason, i) => (
                      <li key={i}>{reason}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Re-evaluation Roadmap */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50/60 p-5">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white shadow-sm ring-1 ring-slate-200 text-brand-700">
                <CalendarCheck className="h-5 w-5" />
              </span>
              <div>
                <h5 className="text-sm font-semibold text-slate-900">Follow-up Re-testing Protocol</h5>
                <p className="text-xs text-slate-500">
                  Allow 8 to 12 weeks of consistent food-first protocol before repeat laboratory blood testing.
                </p>
              </div>
            </div>
            <span className="shrink-0 rounded-md bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700 ring-1 ring-inset ring-brand-200">
              Retest in 8–12 Weeks
            </span>
          </div>

          {/* Non-diagnostic Disclaimer */}
          <p className="border-t border-slate-200 pt-4 text-xs leading-relaxed text-slate-500 italic">
            Disclaimer: NutriLens is an educational nutrition-support tool grounded in ICMR-NIN reference data. It does not provide medical diagnoses, treatment plans, or clinical pharmaceutical prescriptions. Always consult a qualified physician or healthcare provider before altering your health regimen.
          </p>
        </div>
      </Card>
    </div>
  );
};
