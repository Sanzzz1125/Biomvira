"""
Unit conversion utilities for clinical blood biomarkers.
Ensures all values are converted to canonical units before range comparison.
"""
from typing import Tuple

CONVERSION_FACTORS = {
    "vitamin_d": {
        "canonical": "ng/mL",
        "conversions": {
            "ng/ml": 1.0,
            "ng/milliliter": 1.0,
            "nmol/l": 1.0 / 2.496,  # 1 ng/mL = 2.496 nmol/L
            "nmol/liter": 1.0 / 2.496,
            "ug/l": 1.0
        }
    },
    "vitamin_b12": {
        "canonical": "pg/mL",
        "conversions": {
            "pg/ml": 1.0,
            "pg/milliliter": 1.0,
            "pmol/l": 1.0 / 0.7378, # 1 pg/mL = 0.7378 pmol/L
            "pmol/liter": 1.0 / 0.7378,
            "ng/l": 1.0
        }
    },
    "folate": {
        "canonical": "ng/mL",
        "conversions": {
            "ng/ml": 1.0,
            "nmol/l": 1.0 / 2.266,  # 1 ng/mL = 2.266 nmol/L
            "ug/l": 1.0
        }
    },
    "ferritin": {
        "canonical": "ng/mL",
        "conversions": {
            "ng/ml": 1.0,
            "µg/l": 1.0,
            "ug/l": 1.0,
            "mcg/l": 1.0
        }
    },
    "hemoglobin": {
        "canonical": "g/dL",
        "conversions": {
            "g/dl": 1.0,
            "g/100ml": 1.0,
            "g/l": 0.1,             # 1 g/dL = 10 g/L -> g/L * 0.1 = g/dL
            "gm/dl": 1.0,
            "gms/dl": 1.0,
            "g%": 1.0,
            "gm%": 1.0,
            "gm/100ml": 1.0
        }
    },
    "calcium": {
        "canonical": "mg/dL",
        "conversions": {
            "mg/dl": 1.0,
            "mg%": 1.0,
            "mmol/l": 4.008,        # 1 mmol/L = 4.008 mg/dL
            "meq/l": 2.004          # 1 mEq/L = 2.004 mg/dL
        }
    },
    # --- blood sugar -------------------------------------------------------------------------------------------
    # A conversion is a multiplier, or a (multiplier, offset) pair for formulas such as HbA1c.
    "hba1c": {
        "canonical": "%",
        "conversions": {
            "%": 1.0,
            "mmol/mol": (0.0915, 2.15),   # IFCC mmol/mol -> NGSP %: % = 0.0915 x mmol/mol + 2.15
        }
    },
    "fasting_glucose": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "mmol/l": 18.016}},
    "postprandial_glucose": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "mmol/l": 18.016}},
    # --- blood fats --------------------------------------------------------------------------------------------
    "total_cholesterol": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "mmol/l": 38.67}},
    "ldl_cholesterol": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "mmol/l": 38.67}},
    "hdl_cholesterol": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "mmol/l": 38.67}},
    "triglycerides": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "mmol/l": 88.57}},
    # --- kidney ------------------------------------------------------------------------------------------------
    "creatinine": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "umol/l": 1.0 / 88.4}},
    "urea": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "mmol/l": 6.006}},
    "uric_acid": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "umol/l": 1.0 / 59.48}},
    # --- liver -------------------------------------------------------------------------------------------------
    "sgot_ast": {"canonical": "U/L", "conversions": {"u/l": 1.0, "iu/l": 1.0}},
    "sgpt_alt": {"canonical": "U/L", "conversions": {"u/l": 1.0, "iu/l": 1.0}},
    "alkaline_phosphatase": {"canonical": "U/L", "conversions": {"u/l": 1.0, "iu/l": 1.0}},
    "bilirubin_total": {"canonical": "mg/dL", "conversions": {"mg/dl": 1.0, "mg%": 1.0, "umol/l": 1.0 / 17.1}},
    "total_protein": {"canonical": "g/dL", "conversions": {"g/dl": 1.0, "gm/dl": 1.0, "gms/dl": 1.0, "g%": 1.0, "gm%": 1.0, "g/l": 0.1}},
    "albumin": {"canonical": "g/dL", "conversions": {"g/dl": 1.0, "gm/dl": 1.0, "gms/dl": 1.0, "g%": 1.0, "gm%": 1.0, "g/l": 0.1}},
}

def clean_unit_string(unit: str) -> str:
    """Normalize unit string: lowercase, remove spaces, unify micro symbol."""
    if not unit:
        return ""
    u = unit.strip().lower()
    u = u.replace(" ", "")
    u = u.replace("μ", "u").replace("µ", "u")
    return u

def convert_to_canonical(biomarker_key: str, value: float, unit: str) -> Tuple[float, str]:
    """
    Converts a biomarker value to its canonical unit.
    Returns (canonical_value, canonical_unit).
    """
    import math
    if not math.isfinite(value) or value < 0:
        raise ValueError("Invalid measurement")
    cleaned_unit = clean_unit_string(unit)
    bio_config = CONVERSION_FACTORS.get(biomarker_key)
    
    if not bio_config:
        raise ValueError("Unsupported biomarker")
    
    canonical_unit = bio_config["canonical"]
    conversions = bio_config["conversions"]
    
    factor = conversions.get(cleaned_unit)
    if factor is not None:
        multiplier, offset = factor if isinstance(factor, tuple) else (factor, 0.0)
        converted_value = round(value * multiplier + offset, 2)
        return converted_value, canonical_unit
    
    raise ValueError(f"Unsupported unit for {biomarker_key}: {unit or 'missing'}")
