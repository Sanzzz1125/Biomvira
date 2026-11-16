import React from 'react';
import { ArrowLeft, ArrowRight, Eye, EyeOff, Plus, ShieldCheck, Trash2 } from 'lucide-react';
import { DetectedBiomarker } from '../types';
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
  { key: 'vitamin_d', name: 'Vitamin D (25-OH)', canonicalUnit: 'ng/mL' },
  { key: 'vitamin_b12', name: 'Vitamin B12 (Cobalamin)', canonicalUnit: 'pg/mL' },
  { key: 'folate', name: 'Folate (Vitamin B9)', canonicalUnit: 'ng/mL' },
  { key: 'ferritin', name: 'Serum Ferritin', canonicalUnit: 'ng/mL' },
  { key: 'hemoglobin', name: 'Hemoglobin (Hb)', canonicalUnit: 'g/dL' },
  { key: 'calcium', name: 'Serum Calcium', canonicalUnit: 'mg/dL' },
  { key: 'hba1c', name: 'HbA1c (Glycated Haemoglobin)', canonicalUnit: '%' },
  { key: 'fasting_glucose', name: 'Fasting Blood Glucose', canonicalUnit: 'mg/dL' },
  { key: 'postprandial_glucose', name: 'Post-Meal Blood Glucose', canonicalUnit: 'mg/dL' },
  { key: 'total_cholesterol', name: 'Total Cholesterol', canonicalUnit: 'mg/dL' },
  { key: 'triglycerides', name: 'Triglycerides', canonicalUnit: 'mg/dL' },
  { key: 'ldl_cholesterol', name: 'LDL Cholesterol', canonicalUnit: 'mg/dL' },
  { key: 'hdl_cholesterol', name: 'HDL Cholesterol', canonicalUnit: 'mg/dL' },
  { key: 'creatinine', name: 'Serum Creatinine', canonicalUnit: 'mg/dL' },
  { key: 'urea', name: 'Blood Urea', canonicalUnit: 'mg/dL' },
  { key: 'uric_acid', name: 'Serum Uric Acid', canonicalUnit: 'mg/dL' },
  { key: 'sgot_ast', name: 'SGOT / AST', canonicalUnit: 'U/L' },
  { key: 'sgpt_alt', name: 'SGPT / ALT', canonicalUnit: 'U/L' },
  { key: 'alkaline_phosphatase', name: 'Alkaline Phosphatase', canonicalUnit: 'U/L' },
  { key: 'bilirubin_total', name: 'Total Bilirubin', canonicalUnit: 'mg/dL' },
  { key: 'total_protein', name: 'Total Protein', canonicalUnit: 'g/dL' },
  { key: 'albumin', name: 'Serum Albumin', canonicalUnit: 'g/dL' },
];

const GRID = 'md:grid md:grid-cols-[minmax(0,2fr)_minmax(0,1.1fr)_minmax(0,0.9fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_40px] md:items-center md:gap-4';

const MobileLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span className="mb-1 block text-xs font-medium text-slate-500 md:hidden">{children}</span>
);

export const VerificationTable: React.FC<VerificationTableProps> = ({
  markers,
  warnings = [],
  setMarkers,
  sanitizedPreview,
  onProceedToProfile,
  onReset,
}) => {
  const [confirmed, setConfirmed] = React.useState(false);
  React.useEffect(() => setConfirmed(false), [markers]);
  const [showSanitized, setShowSanitized] = React.useState(false);

  const handleValueChange = (index: number, val: number) => {
    setMarkers((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], detected_value: val, canonical_value: val, qualifier: null };
      return next;
    });
  };

  const handleUnitChange = (index: number, unit: string) => {
    setMarkers((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], detected_unit: unit };
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

  const methodBadge = (method: string) => {
    if (method === 'llm_fallback') return <Badge tone="indigo">AI-assisted</Badge>;
    if (method === 'manual') return <Badge>Added by you</Badge>;
    return <Badge tone="brand">Auto</Badge>;
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        eyebrow="Step 2 of 4"
        title="Check your results"
        description="We found these values in your report. Please confirm they match your lab slip, and correct anything that looks off."
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

      {warnings.map((warning, i) => <p role="status" className="text-sm text-amber-800" key={i}>{warning}</p>)}
      <label
        className={cx(
          'flex cursor-pointer items-start gap-3 rounded-xl border-2 p-4 shadow-card transition-colors',
          confirmed ? 'border-brand-300 bg-brand-50' : 'border-amber-300 bg-amber-50',
        )}
      >
        <input
          type="checkbox"
          checked={confirmed}
          onChange={e => setConfirmed(e.target.checked)}
          className="mt-0.5 h-5 w-5 shrink-0 cursor-pointer accent-brand-600"
        />
        <span className="text-sm leading-relaxed">
          <span className={cx('block font-semibold', confirmed ? 'text-brand-800' : 'text-amber-900')}>
            I checked every value and unit against the report and resolved warnings.
          </span>
          <span className={cx('mt-1 block', confirmed ? 'text-brand-700' : 'text-amber-800')}>
            Qualified bounds must be removed or replaced with an exact result.
          </span>
        </span>
      </label>
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
            {markers.map((marker, idx) => {
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
                    'grid grid-cols-2 gap-x-4 gap-y-4 px-5 py-5 transition-colors hover:bg-slate-50/70 md:px-6 md:py-4'
                  )}
                >
                  <div className="col-span-2 flex items-start justify-between gap-3 md:col-span-1 md:block">
                    <div>
                      <p className="text-[15px] font-semibold text-slate-900">{marker.display_name}</p>
                      {isOutOfRange && (
                        <p className="mt-0.5 text-xs font-medium text-amber-700">Outside reference range</p>
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
                    <span className="text-xs text-slate-500 tabular-nums">
                      {marker.verification_status || "needs_review"}{marker.source_page ? ` · Page ${marker.source_page}` : ""}
                      {marker.qualifier && <span> · Reported {marker.qualifier}{marker.detected_value}</span>}
                      {marker.warnings?.map((warning, i) => <span className="block text-amber-700" key={i}>{warning}</span>)}
                    </span>
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
          <div className="flex flex-wrap items-center gap-2 border-t border-slate-200 bg-slate-50 px-5 py-4 md:px-6">
            <span className="mr-1 text-sm font-medium text-slate-600">Add a biomarker</span>
            {unaddedBiomarkers.map((b) => (
              <button
                key={b.key}
                type="button"
                onClick={() => handleAddMarker(b.key)}
                className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-white px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:border-brand-400 hover:bg-brand-50 hover:text-brand-700"
              >
                <Plus className="h-3.5 w-3.5" aria-hidden />
                {b.name}
              </button>
            ))}
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
          disabled={!confirmed || markers.length === 0 || markers.some(m => !m.detected_unit.trim() || m.qualifier || !Number.isFinite(m.detected_value)) || new Set(markers.map(m => m.biomarker_key)).size !== markers.length}
          iconRight={<ArrowRight className="h-4 w-4" aria-hidden />}
        >
          Continue
        </Button>
      </div>
    </div>
  );
};
