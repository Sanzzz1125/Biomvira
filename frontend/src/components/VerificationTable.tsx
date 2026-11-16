import React from 'react';
import { AlertTriangle, ArrowLeft, ArrowRight, Eye, EyeOff, Info, Plus, ShieldCheck, Trash2 } from 'lucide-react';
import { DetectedBiomarker } from '../types';
import { isBlocking, reviewReason } from '../lib/review';
import { Badge, Button, Card, PageHeader, cx } from './ui';

interface VerificationTableProps {
  markers: DetectedBiomarker[];
  warnings?: string[];
  setMarkers: React.Dispatch<React.SetStateAction<DetectedBiomarker[]>>;
  sanitizedPreview?: string;
  onProceedToProfile: () => void;
  onReset: () => void;
}

const AVAILABLE_BIOMARKERS = [
  { key: 'vitamin_d', name: "Vitamin D (25-OH)", canonicalUnit: 'ng/mL', group: 'Fat-Soluble Vitamin' },
  { key: 'vitamin_b12', name: "Vitamin B12 (Cobalamin)", canonicalUnit: 'pg/mL', group: 'Water-Soluble Vitamin' },
  { key: 'folate', name: "Folate (Vitamin B9)", canonicalUnit: 'ng/mL', group: 'Water-Soluble Vitamin' },
  { key: 'ferritin', name: "Serum Ferritin (Iron Storage)", canonicalUnit: 'ng/mL', group: 'Mineral Storage' },
  { key: 'hemoglobin', name: "Hemoglobin (Hb)", canonicalUnit: 'g/dL', group: 'Hematology' },
  { key: 'calcium', name: "Serum Calcium", canonicalUnit: 'mg/dL', group: 'Mineral' },
  { key: 'hba1c', name: "HbA1c (Glycated Haemoglobin)", canonicalUnit: '%', group: 'Blood Sugar Control' },
  { key: 'fasting_glucose', name: "Fasting Blood Glucose", canonicalUnit: 'mg/dL', group: 'Blood Sugar Control' },
  { key: 'postprandial_glucose', name: "Post-Meal (Post-Prandial) Blood Glucose", canonicalUnit: 'mg/dL', group: 'Blood Sugar Control' },
  { key: 'total_cholesterol', name: "Total Cholesterol", canonicalUnit: 'mg/dL', group: 'Blood Fats (Lipids)' },
  { key: 'triglycerides', name: "Triglycerides", canonicalUnit: 'mg/dL', group: 'Blood Fats (Lipids)' },
  { key: 'ldl_cholesterol', name: "LDL Cholesterol", canonicalUnit: 'mg/dL', group: 'Blood Fats (Lipids)' },
  { key: 'hdl_cholesterol', name: "HDL Cholesterol", canonicalUnit: 'mg/dL', group: 'Blood Fats (Lipids)' },
  { key: 'creatinine', name: "Serum Creatinine", canonicalUnit: 'mg/dL', group: 'Kidney Function' },
  { key: 'urea', name: "Blood Urea", canonicalUnit: 'mg/dL', group: 'Kidney Function' },
  { key: 'uric_acid', name: "Serum Uric Acid", canonicalUnit: 'mg/dL', group: 'Kidney Function' },
  { key: 'sgot_ast', name: "SGOT / AST", canonicalUnit: 'U/L', group: 'Liver Function' },
  { key: 'sgpt_alt', name: "SGPT / ALT", canonicalUnit: 'U/L', group: 'Liver Function' },
  { key: 'alkaline_phosphatase', name: "Alkaline Phosphatase", canonicalUnit: 'U/L', group: 'Liver Function' },
  { key: 'bilirubin_total', name: "Total Bilirubin", canonicalUnit: 'mg/dL', group: 'Liver Function' },
  { key: 'total_protein', name: "Total Protein", canonicalUnit: 'g/dL', group: 'Liver Function' },
  { key: 'albumin', name: "Serum Albumin", canonicalUnit: 'g/dL', group: 'Liver Function' },
  { key: 'wbc', name: "Total WBC Count (TLC)", canonicalUnit: 'cells/µL', group: 'Complete Blood Count' },
  { key: 'rbc', name: "RBC Count", canonicalUnit: 'million/µL', group: 'Complete Blood Count' },
  { key: 'platelets', name: "Platelet Count", canonicalUnit: '×10³/µL', group: 'Complete Blood Count' },
  { key: 'pcv', name: "Hematocrit (PCV)", canonicalUnit: '%', group: 'Complete Blood Count' },
  { key: 'mcv', name: "MCV (Mean Cell Volume)", canonicalUnit: 'fL', group: 'Complete Blood Count' },
  { key: 'mch', name: "MCH (Mean Cell Haemoglobin)", canonicalUnit: 'pg', group: 'Complete Blood Count' },
  { key: 'mchc', name: "MCHC", canonicalUnit: 'g/dL', group: 'Complete Blood Count' },
  { key: 'rdw', name: "RDW-CV", canonicalUnit: '%', group: 'Complete Blood Count' },
  { key: 'mpv', name: "Mean Platelet Volume (MPV)", canonicalUnit: 'fL', group: 'Complete Blood Count' },
  { key: 'neutrophils', name: "Neutrophils (%)", canonicalUnit: '%', group: 'Complete Blood Count' },
  { key: 'neutrophils_abs', name: "Absolute Neutrophil Count", canonicalUnit: 'cells/µL', group: 'Complete Blood Count' },
  { key: 'lymphocytes', name: "Lymphocytes (%)", canonicalUnit: '%', group: 'Complete Blood Count' },
  { key: 'lymphocytes_abs', name: "Absolute Lymphocyte Count", canonicalUnit: 'cells/µL', group: 'Complete Blood Count' },
  { key: 'eosinophils', name: "Eosinophils (%)", canonicalUnit: '%', group: 'Complete Blood Count' },
  { key: 'eosinophils_abs', name: "Absolute Eosinophil Count", canonicalUnit: 'cells/µL', group: 'Complete Blood Count' },
  { key: 'monocytes', name: "Monocytes (%)", canonicalUnit: '%', group: 'Complete Blood Count' },
  { key: 'monocytes_abs', name: "Absolute Monocyte Count", canonicalUnit: 'cells/µL', group: 'Complete Blood Count' },
  { key: 'basophils', name: "Basophils (%)", canonicalUnit: '%', group: 'Complete Blood Count' },
  { key: 'basophils_abs', name: "Absolute Basophil Count", canonicalUnit: 'cells/µL', group: 'Complete Blood Count' },
  { key: 'esr', name: "ESR", canonicalUnit: 'mm/hr', group: 'Complete Blood Count' },
  { key: 'tsh', name: "TSH (Thyroid Stimulating Hormone)", canonicalUnit: 'µIU/mL', group: 'Thyroid Function' },
  { key: 't3', name: "Total T3", canonicalUnit: 'ng/dL', group: 'Thyroid Function' },
  { key: 't4', name: "Total T4", canonicalUnit: 'µg/dL', group: 'Thyroid Function' },
  { key: 'ft3', name: "Free T3", canonicalUnit: 'pg/mL', group: 'Thyroid Function' },
  { key: 'ft4', name: "Free T4", canonicalUnit: 'ng/dL', group: 'Thyroid Function' },
  { key: 'sodium', name: "Sodium", canonicalUnit: 'mmol/L', group: 'Electrolytes' },
  { key: 'potassium', name: "Potassium", canonicalUnit: 'mmol/L', group: 'Electrolytes' },
  { key: 'chloride', name: "Chloride", canonicalUnit: 'mmol/L', group: 'Electrolytes' },
  { key: 'serum_iron', name: "Serum Iron", canonicalUnit: 'µg/dL', group: 'Iron Studies' },
  { key: 'tibc', name: "TIBC (Total Iron Binding Capacity)", canonicalUnit: 'µg/dL', group: 'Iron Studies' },
  { key: 'transferrin_saturation', name: "Transferrin Saturation", canonicalUnit: '%', group: 'Iron Studies' },
  { key: 'ggt', name: "GGT (Gamma GT)", canonicalUnit: 'U/L', group: 'Liver Function' },
  { key: 'bilirubin_direct', name: "Direct Bilirubin", canonicalUnit: 'mg/dL', group: 'Liver Function' },
  { key: 'bilirubin_indirect', name: "Indirect Bilirubin", canonicalUnit: 'mg/dL', group: 'Liver Function' },
  { key: 'globulin', name: "Globulin", canonicalUnit: 'g/dL', group: 'Liver Function' },
  { key: 'bun', name: "Blood Urea Nitrogen (BUN)", canonicalUnit: 'mg/dL', group: 'Kidney Function' },
  { key: 'egfr', name: "eGFR", canonicalUnit: 'mL/min/1.73m²', group: 'Kidney Function' },
  { key: 'phosphorus', name: "Phosphorus", canonicalUnit: 'mg/dL', group: 'Kidney Function' },
  { key: 'crp', name: "C-Reactive Protein (CRP)", canonicalUnit: 'mg/L', group: 'Inflammation' },
];

const GRID = 'md:grid md:grid-cols-[minmax(0,2fr)_minmax(0,1.1fr)_minmax(0,0.9fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_40px] md:items-center md:gap-4';

const MobileLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span className="mb-1 block text-xs font-medium text-slate-500 md:hidden">{children}</span>
);

const edited = (m: DetectedBiomarker) => (m.extraction_method === 'manual' ? 'manual' : 'edited');

export const VerificationTable: React.FC<VerificationTableProps> = ({
  markers,
  warnings = [],
  setMarkers,
  sanitizedPreview,
  onProceedToProfile,
  onReset,
}) => {
  const [showSanitized, setShowSanitized] = React.useState(false);

  const handleValueChange = (index: number, val: number) => {
    setMarkers((prev) => {
      const next = [...prev];
      // An edited value is the person's own reading of the report, so earlier extraction notes no longer apply.
      next[index] = { ...next[index], detected_value: val, canonical_value: val, qualifier: null, warnings: [], extraction_method: edited(next[index]) };
      return next;
    });
  };

  const handleUnitChange = (index: number, unit: string) => {
    setMarkers((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], detected_unit: unit, canonical_value: next[index].detected_value, warnings: [], extraction_method: edited(next[index]) };
      return next;
    });
  };

  const handleRangeChange = (index: number, field: 'low' | 'high', val: string) => {
    const num = val === '' ? null : parseFloat(val);
    setMarkers((prev) => {
      const next = [...prev];
      const curRange = next[index].report_reference_range || { low: null, high: null };
      next[index] = {
        ...next[index],
        report_reference_range: {
          ...curRange,
          [field]: num,
        },
      };
      return next;
    });
  };

  const handleDelete = (index: number) => {
    setMarkers((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAddMarker = (key: string) => {
    const found = AVAILABLE_BIOMARKERS.find((b) => b.key === key);
    if (!found) return;

    if (markers.some((m) => m.biomarker_key === key)) {
      return;
    }

    const newMarker: DetectedBiomarker = {
      biomarker_key: found.key,
      display_name: found.name,
      detected_value: 0.0,
      detected_unit: found.canonicalUnit,
      canonical_value: 0.0,
      canonical_unit: found.canonicalUnit,
      report_reference_range: { low: null, high: null },
      extraction_method: 'manual',
      confidence: 1.0,
    };

    setMarkers((prev) => [...prev, newMarker]);
  };

  const unaddedBiomarkers = AVAILABLE_BIOMARKERS.filter(
    (b) => !markers.some((m) => m.biomarker_key === b.key)
  );

  const attentionCount = markers.filter((m) => reviewReason(m, markers)).length;
  const blocked = markers.length === 0 || markers.some((m) => isBlocking(m, markers));
  // Results that need attention are listed first; the rest keep the report's order.
  const ordered = markers
    .map((marker, idx) => ({ marker, idx }))
    .sort((a, b) => Number(!reviewReason(a.marker, markers)) - Number(!reviewReason(b.marker, markers)));

  const methodBadge = (method: string) => {
    if (method === 'llm_fallback') return <Badge tone="indigo">AI-assisted</Badge>;
    if (method === 'manual') return <Badge>Added by you</Badge>;
    if (method === 'edited') return <Badge>Edited</Badge>;
    return <Badge tone="brand">Auto</Badge>;
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        eyebrow="Review results"
        title={attentionCount > 0 ? `${attentionCount} ${attentionCount === 1 ? 'result needs' : 'results need'} your attention` : 'Your results'}
        description={
          attentionCount > 0
            ? `We read ${markers.length} results from your report. The highlighted ones could not be confirmed automatically; everything else is ready.`
            : `We read ${markers.length} results from your report. You can correct a value or add a missing test before continuing.`
        }
        actions={
          <>
            {sanitizedPreview && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowSanitized(!showSanitized)}
                aria-expanded={showSanitized}
                icon={showSanitized ? <EyeOff className="h-4 w-4" aria-hidden /> : <Eye className="h-4 w-4" aria-hidden />}
              >
                {showSanitized ? 'Hide' : 'View'} anonymised text
              </Button>
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={onReset}
              icon={<ArrowLeft className="h-4 w-4" aria-hidden />}
            >
              Start over
            </Button>
          </>
        }
      />

      {showSanitized && sanitizedPreview && (
        <Card className="animate-fade-in p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-brand-700">
            <ShieldCheck className="h-4 w-4" aria-hidden />
            Personal details removed
          </div>
          <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 font-mono text-xs leading-relaxed text-slate-600 ring-1 ring-inset ring-slate-200">
            {sanitizedPreview}
          </pre>
        </Card>
      )}

      {warnings.length > 0 && (
        <Card className="flex items-start gap-3 border-sky-200 bg-sky-50/60 p-4">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-sky-700" aria-hidden />
          <ul className="space-y-1 text-sm text-sky-900">
            {warnings.map((warning, i) => (
              <li key={i}>{warning}</li>
            ))}
          </ul>
        </Card>
      )}
      <Card className="overflow-hidden">
        {/* Column headings (desktop) */}
        <div
          className={cx(
            GRID,
            'hidden border-b border-slate-200 bg-slate-50 px-6 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500'
          )}
        >
          <span>Biomarker</span>
          <span>Your value</span>
          <span>Unit</span>
          <span>Reference range</span>
          <span>Source</span>
          <span className="sr-only">Remove</span>
        </div>

        {markers.length === 0 ? (
          <div className="px-6 py-14 text-center">
            <p className="text-[15px] font-semibold text-slate-900">No biomarkers detected</p>
            <p className="mt-1 text-sm text-slate-500">
              Add the values from your report manually using the options below.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-slate-200">
            {ordered.map(({ marker, idx }) => {
              const reason = reviewReason(marker, markers);
              const refLow = marker.report_reference_range?.low;
              const refHigh = marker.report_reference_range?.high;
              const isOutOfRange =
                (refLow !== null && refLow !== undefined && marker.detected_value < refLow) ||
                (refHigh !== null && refHigh !== undefined && marker.detected_value > refHigh);
              const id = marker.biomarker_key;

              return (
                <li
                  key={`${id}-${idx}`}
                  className={cx(
                    GRID,
                    'grid grid-cols-2 gap-x-4 gap-y-4 px-5 py-5 transition-colors md:px-6 md:py-4',
                    reason ? 'bg-amber-50/60' : 'hover:bg-slate-50/70'
                  )}
                >
                  <div className="col-span-2 flex items-start justify-between gap-3 md:col-span-1 md:block">
                    <div>
                      <p className="text-[15px] font-semibold text-slate-900">{marker.display_name}</p>
                      {reason ? (
                        <p className="mt-1 flex items-start gap-1.5 text-xs font-medium text-amber-800">
                          <AlertTriangle className="mt-px h-3.5 w-3.5 shrink-0" aria-hidden />
                          {reason}
                        </p>
                      ) : (
                        isOutOfRange && <p className="mt-0.5 text-xs font-medium text-slate-500">Outside reference range</p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDelete(idx)}
                      aria-label={`Remove ${marker.display_name}`}
                      className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600 md:hidden"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden />
                    </button>
                  </div>

                  <div>
                    <MobileLabel>Your value</MobileLabel>
                    <input
                      type="number"
                      step="any"
                      aria-label={`${marker.display_name} value`}
                      value={marker.detected_value}
                      onChange={(e) => handleValueChange(idx, parseFloat(e.target.value) || 0)}
                      className={cx(
                        'field font-semibold tabular-nums',
                        isOutOfRange && 'border-amber-400 bg-amber-50/50 text-amber-900 focus:border-amber-500 focus:ring-amber-500/20'
                      )}
                    />
                  </div>

                  <div>
                    <MobileLabel>Unit</MobileLabel>
                    <input
                      type="text"
                      aria-label={`${marker.display_name} unit`}
                      value={marker.detected_unit}
                      onChange={(e) => handleUnitChange(idx, e.target.value)}
                      className="field"
                    />
                  </div>

                  <div className="col-span-2 md:col-span-1">
                    <MobileLabel>Reference range</MobileLabel>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        step="any"
                        placeholder="Low"
                        aria-label={`${marker.display_name} reference low`}
                        value={marker.report_reference_range?.low ?? ''}
                        onChange={(e) => handleRangeChange(idx, 'low', e.target.value)}
                        className="field min-w-0 text-center tabular-nums"
                      />
                      <span className="text-slate-400" aria-hidden>
                        –
                      </span>
                      <input
                        type="number"
                        step="any"
                        placeholder="High"
                        aria-label={`${marker.display_name} reference high`}
                        value={marker.report_reference_range?.high ?? ''}
                        onChange={(e) => handleRangeChange(idx, 'high', e.target.value)}
                        className="field min-w-0 text-center tabular-nums"
                      />
                    </div>
                  </div>

                  <div className="col-span-2 flex items-center gap-2 md:col-span-1">
                    {methodBadge(marker.extraction_method)}
                    {marker.source_page ? (
                      <span className="text-xs text-slate-500 tabular-nums">Page {marker.source_page}</span>
                    ) : null}
                  </div>

                  <div className="hidden justify-end md:flex">
                    <button
                      type="button"
                      onClick={() => handleDelete(idx)}
                      aria-label={`Remove ${marker.display_name}`}
                      className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden />
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}

        {unaddedBiomarkers.length > 0 && (
          <div className="flex flex-wrap items-center gap-3 border-t border-slate-200 bg-slate-50 px-5 py-4 md:px-6">
            <label htmlFor="add-biomarker" className="flex items-center gap-1.5 text-sm font-medium text-slate-600">
              <Plus className="h-4 w-4" aria-hidden />
              Add a test from your report
            </label>
            <select
              id="add-biomarker"
              value=""
              onChange={(e) => handleAddMarker(e.target.value)}
              className="field w-full sm:w-auto sm:min-w-[18rem]"
            >
              <option value="" disabled>
                Choose a test…
              </option>
              {[...new Set(unaddedBiomarkers.map((b) => b.group))].map((group) => (
                <optgroup key={group} label={group}>
                  {unaddedBiomarkers
                    .filter((b) => b.group === group)
                    .map((b) => (
                      <option key={b.key} value={b.key}>
                        {b.name}
                      </option>
                    ))}
                </optgroup>
              ))}
            </select>
          </div>
        )}
      </Card>

      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-slate-500">
          <span className="font-semibold text-slate-900 tabular-nums">{markers.length}</span>{' '}
          {markers.length === 1 ? 'biomarker' : 'biomarkers'} to review
        </p>
        <Button
          size="lg"
          onClick={onProceedToProfile}
          disabled={blocked}
          iconRight={<ArrowRight className="h-4 w-4" aria-hidden />}
        >
          Continue
        </Button>
      </div>
    </div>
  );
};
