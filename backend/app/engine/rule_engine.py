import json
import os
from typing import Dict, Any, Optional
from app.models.schemas import MarkerInput, MarkerAnalysisResult, MarkerStatus, UserProfile
from app.engine.unit_converter import convert_to_canonical

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "biomarkers.json")

def load_biomarkers_data() -> Dict[str, Any]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {b["key"]: b for b in data["biomarkers"]}

BIOMARKERS_CONFIG = load_biomarkers_data()

class RuleEngine:
    @staticmethod
    def _display_ceiling(value: float) -> float:
        """Bands are stored as 99.99 so that 99.995 falls in the next band; show the familiar whole number (99)."""
        return float(int(value)) if abs(value - int(value) - 0.99) < 1e-9 else value

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or BIOMARKERS_CONFIG

    def evaluate_marker(self, marker: MarkerInput, profile: UserProfile) -> MarkerAnalysisResult:
        bio_info = self.config.get(marker.biomarker_key)
        if not bio_info:
            raise ValueError(f"Unknown biomarker key: {marker.biomarker_key}")

        canonical_val, canonical_unit = convert_to_canonical(
            marker.biomarker_key, marker.value, marker.unit
        )

        # 1. Determine reference intervals
        direction = bio_info.get("direction", "lower_is_worse")
        intervals = bio_info.get("standard_intervals", {})
        gender_key = profile.gender.lower() if profile.gender.lower() in ["male", "female"] else "female"
        target_interval = intervals.get(gender_key) or intervals.get("adult") or next(iter(intervals.values()), {})
        normal_band = target_interval.get("normal", {})
        borderline_band = target_interval.get("borderline", {})
        high_band = target_interval.get("high", {})

        raw_low = marker.reference_low
        raw_high = marker.reference_high
        lab_low, lab_high = None, None

        if raw_low is not None:
            lab_low, _ = convert_to_canonical(marker.biomarker_key, raw_low, marker.unit)
        if raw_high is not None:
            lab_high, _ = convert_to_canonical(marker.biomarker_key, raw_high, marker.unit)

        # Retain reporting lab interval when provided
        has_custom_report_range = (lab_low is not None or lab_high is not None)

        if has_custom_report_range:
            range_low = lab_low if lab_low is not None else 0.0
            range_high = lab_high if lab_high is not None else max(normal_band.get("max", range_low), range_low)
        else:
            range_low = normal_band.get("min", 0.0)
            range_high = normal_band.get("max", 100.0)

        # Guideline metadata (kept separate and traceable from laboratory intervals)
        guideline = bio_info.get("clinical_guideline") or {}
        guideline_threshold = guideline.get("threshold")
        guideline_source = guideline.get("source")

        # 2. Status Classification
        status = MarkerStatus.NORMAL
        if direction == "higher_is_worse":
            normal_floor = normal_band.get("min", 0.0)
            high_cut = high_band.get("min", range_high)
            guideline_normal_max = normal_band.get("max", range_high)

            if normal_floor > 0 and canonical_val < normal_floor:
                status = MarkerStatus.LOW
            elif canonical_val >= high_cut:
                status = MarkerStatus.HIGH
            elif canonical_val <= guideline_normal_max and canonical_val <= range_high:
                status = MarkerStatus.NORMAL
            else:
                status = MarkerStatus.BORDERLINE
        elif direction == "two_sided":
            if canonical_val < range_low:
                status = MarkerStatus.LOW
            elif canonical_val > range_high:
                status = MarkerStatus.HIGH
        elif not has_custom_report_range and borderline_band:
            b_min = borderline_band.get("min", range_low)
            b_max = borderline_band.get("max", range_low)
            if canonical_val < b_min:
                status = MarkerStatus.LOW
            elif b_min <= canonical_val <= b_max:
                status = MarkerStatus.BORDERLINE
            elif canonical_val > range_high:
                status = MarkerStatus.HIGH
            else:
                status = MarkerStatus.NORMAL
        else:
            borderline_margin = (range_high - range_low) * 0.05
            if canonical_val < range_low:
                status = MarkerStatus.LOW
            elif range_low <= canonical_val <= (range_low + borderline_margin):
                status = MarkerStatus.BORDERLINE
            elif canonical_val > range_high:
                status = MarkerStatus.HIGH
            else:
                status = MarkerStatus.NORMAL

        # 3. Clinical Warning Threshold
        clinical_warning = None
        warning_thresh = bio_info.get("clinical_warning_threshold")
        if warning_thresh is not None and canonical_val <= warning_thresh:
            clinical_warning = bio_info.get("clinical_warning_message")
        high_thresh = bio_info.get("clinical_warning_high_threshold")
        if high_thresh is not None and canonical_val >= high_thresh:
            clinical_warning = bio_info.get("clinical_warning_message")
        if clinical_warning is None and status == MarkerStatus.LOW and bio_info.get("low_status_message"):
            clinical_warning = bio_info["low_status_message"]
        food_plan_on = bio_info.get("food_plan_on") or {}
        factor = bio_info.get("doctor_above_factor")
        if clinical_warning is None and factor and range_high > 0 and canonical_val >= factor * range_high:
            clinical_warning = (f"{bio_info['display_name']} is more than {factor} times the upper limit of its reference "
                                "range. Please see a doctor; diet changes alone are not enough.")
        if (clinical_warning is None and status != MarkerStatus.NORMAL and bio_info.get("abnormal_requires_consult")
                and status.value not in food_plan_on):
            where = "below" if status == MarkerStatus.LOW or (
                status == MarkerStatus.BORDERLINE and direction == "lower_is_worse") else "above"
            clinical_warning = (f"{bio_info['display_name']} is {where} its reference range. NutriLens does not give food advice "
                                "for this test; please review it with your doctor.")

        # 4. Percentage of Optimal calculation
        if direction == "lower_is_worse":
            pct = round((canonical_val / range_low) * 100, 1) if range_low > 0 else 100.0
        elif canonical_val <= 0:
            pct = 100.0
        elif status == MarkerStatus.LOW:
            pct = round((canonical_val / range_low) * 100, 1) if range_low > 0 else 100.0
        else:
            pct = round(min(100.0, (range_high / canonical_val) * 100), 1)

        return MarkerAnalysisResult(
            biomarker_key=marker.biomarker_key,
            display_name=bio_info["display_name"],
            value=canonical_val,
            unit=canonical_unit,
            status=status,
            range_low=round(range_low, 2),
            range_high=round(self._display_ceiling(range_high), 2),
            percentage_of_optimal=pct,
            clinical_warning=clinical_warning,
            target_nutrient_key=food_plan_on.get(status.value) or bio_info.get("target_nutrient_key") or "",
            lab_range_low=round(lab_low, 2) if lab_low is not None else None,
            lab_range_high=round(self._display_ceiling(lab_high), 2) if lab_high is not None else None,
            guideline_threshold=guideline_threshold,
            guideline_source=guideline_source,
        )
