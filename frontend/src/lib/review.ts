import { DetectedBiomarker } from '../types';

/**
 * Which extracted results need the person's attention before analysis.
 *
 * Results read cleanly from the report's text go straight to the plan. A result is only shown for review when it
 * cannot be analysed as it is (missing or unrecognised unit, a "<" or ">" bound, a duplicate) or when it came from a
 * less certain source (a scanned image or the AI helper).
 */
export function reviewReason(marker: DetectedBiomarker, all: DetectedBiomarker[]): string | null {
  if (!Number.isFinite(marker.detected_value)) return 'Enter the value shown on your report.';
  if (!marker.detected_unit.trim()) return 'Add the unit shown on your report.';
  if (marker.canonical_value === null) return `Check the unit: "${marker.detected_unit}" was not recognised.`;
  if (marker.qualifier) return `Reported as ${marker.qualifier}${marker.detected_value}; enter an exact value or remove this test.`;
  if (all.filter((m) => m.biomarker_key === marker.biomarker_key).length > 1)
    return 'This test appears more than once; keep the current result and remove the other.';
  if (marker.extraction_method === 'ocr_regex') return 'Read from a scanned image; please confirm the value.';
  if (marker.extraction_method === 'llm_fallback') return 'Read with the AI helper; please confirm the value.';
  return null;
}

/** Problems that make analysis impossible until they are fixed. */
export function isBlocking(marker: DetectedBiomarker, all: DetectedBiomarker[]): boolean {
  return (
    !Number.isFinite(marker.detected_value) ||
    !marker.detected_unit.trim() ||
    marker.canonical_value === null ||
    !!marker.qualifier ||
    all.filter((m) => m.biomarker_key === marker.biomarker_key).length > 1
  );
}

export function needsReview(markers: DetectedBiomarker[]): boolean {
  return markers.length === 0 || markers.some((m) => reviewReason(m, markers) !== null);
}
