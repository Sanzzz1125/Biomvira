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
        intervals = bio_info.get("standard_intervals", {})
        gender_key = profile.gender.lower() if profile.gender.lower() in ["male", "female"] else "female"
        target_interval = intervals.get(gender_key) or intervals.get("adult") or {}
        normal_band = target_interval.get("normal", {})
        borderline_band = target_interval.get("borderline", {})

        range_low = marker.reference_low
        range_high = marker.reference_high

        has_custom_report_range = range_low is not None and range_high is not None

        if not has_custom_report_range:
            range_low = normal_band.get("min", 0.0)
            range_high = normal_band.get("max", 100.0)
        else:
            # Normalize report ranges if passed in alternate units
            if marker.unit.strip().lower() != canonical_unit.lower():
                range_low, _ = convert_to_canonical(marker.biomarker_key, range_low, marker.unit)
                range_high, _ = convert_to_canonical(marker.biomarker_key, range_high, marker.unit)

        # 2. Status Classification
        status = MarkerStatus.NORMAL
        
        if not has_custom_report_range and borderline_band:
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

        # 4. Percentage of Optimal calculation
        if range_low > 0:
            pct = round((canonical_val / range_low) * 100, 1)
        else:
            pct = 100.0

        return MarkerAnalysisResult(
            biomarker_key=marker.biomarker_key,
            display_name=bio_info["display_name"],
            value=canonical_val,
            unit=canonical_unit,
            status=status,
            range_low=round(range_low, 2),
            range_high=round(range_high, 2),
            percentage_of_optimal=pct,
            clinical_warning=clinical_warning,
            target_nutrient_key=bio_info["target_nutrient_key"]
        )
