"""
Unit conversion utilities for clinical blood biomarkers.
Ensures all values are converted to canonical units before range comparison.
"""
import re
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

# --- common household tests ------------------------------------------------------------------------------------------
# Count units are normalised first (see clean_unit_string): "/cumm", "cells/cu mm" and "/µL" become "/ul";
# "x10^3/µL", "10³/µL" and "thou/µL" become "10^3/ul"; "lakhs/cumm" becomes "lakh/ul"; "million/cumm" becomes "10^6/ul".
CELLS = {"/ul": 1.0, "10^3/ul": 1000.0, "10^9/l": 1000.0}
PERCENT = {"%": 1.0}
G_DL = {"g/dl": 1.0, "gm/dl": 1.0, "gms/dl": 1.0, "g%": 1.0, "gm%": 1.0, "g/l": 0.1}
MG_DL = {"mg/dl": 1.0, "mg%": 1.0}
MMOL = {"mmol/l": 1.0, "meq/l": 1.0}
U_L = {"u/l": 1.0, "iu/l": 1.0}
CONVERSION_FACTORS.update({
    "wbc": {"canonical": "cells/µL", "conversions": CELLS},
    "rbc": {"canonical": "million/µL", "conversions": {"10^6/ul": 1.0, "10^12/l": 1.0, "/ul": 1e-6}},
    "platelets": {"canonical": "×10³/µL", "conversions": {"10^3/ul": 1.0, "10^9/l": 1.0, "lakh/ul": 100.0, "/ul": 0.001}},
    "pcv": {"canonical": "%", "conversions": {"%": 1.0, "l/l": 100.0}},
    "mcv": {"canonical": "fL", "conversions": {"fl": 1.0, "um^3": 1.0, "cu.micron": 1.0}},
    "mch": {"canonical": "pg", "conversions": {"pg": 1.0, "pg/cell": 1.0}},
    "mchc": {"canonical": "g/dL", "conversions": {**G_DL, "%": 1.0}},
    "rdw": {"canonical": "%", "conversions": PERCENT},
    "mpv": {"canonical": "fL", "conversions": {"fl": 1.0}},
    "esr": {"canonical": "mm/hr", "conversions": {"mm/hr": 1.0}},
    "tsh": {"canonical": "µIU/mL", "conversions": {"uiu/ml": 1.0, "miu/l": 1.0, "uu/ml": 1.0, "mu/l": 1.0}},
    "t3": {"canonical": "ng/dL", "conversions": {"ng/dl": 1.0, "ng/ml": 100.0, "nmol/l": 65.1}},
    "t4": {"canonical": "µg/dL", "conversions": {"ug/dl": 1.0, "mcg/dl": 1.0, "nmol/l": 1.0 / 12.87}},
    "ft3": {"canonical": "pg/mL", "conversions": {"pg/ml": 1.0, "pmol/l": 1.0 / 1.536}},
    "ft4": {"canonical": "ng/dL", "conversions": {"ng/dl": 1.0, "pmol/l": 1.0 / 12.87}},
    "sodium": {"canonical": "mmol/L", "conversions": MMOL},
    "potassium": {"canonical": "mmol/L", "conversions": MMOL},
    "chloride": {"canonical": "mmol/L", "conversions": MMOL},
    "serum_iron": {"canonical": "µg/dL", "conversions": {"ug/dl": 1.0, "mcg/dl": 1.0, "umol/l": 5.585}},
    "tibc": {"canonical": "µg/dL", "conversions": {"ug/dl": 1.0, "mcg/dl": 1.0, "umol/l": 5.585}},
    "transferrin_saturation": {"canonical": "%", "conversions": PERCENT},
    "ggt": {"canonical": "U/L", "conversions": U_L},
    "bilirubin_direct": {"canonical": "mg/dL", "conversions": {**MG_DL, "umol/l": 1.0 / 17.1}},
    "bilirubin_indirect": {"canonical": "mg/dL", "conversions": {**MG_DL, "umol/l": 1.0 / 17.1}},
    "globulin": {"canonical": "g/dL", "conversions": G_DL},
    "bun": {"canonical": "mg/dL", "conversions": {**MG_DL, "mmol/l": 2.801}},
    "egfr": {"canonical": "mL/min/1.73m²", "conversions": {"ml/min/1.73m2": 1.0, "ml/min/1.73m^2": 1.0, "ml/min": 1.0}},
    "phosphorus": {"canonical": "mg/dL", "conversions": {**MG_DL, "mmol/l": 3.097}},
    "crp": {"canonical": "mg/L", "conversions": {"mg/l": 1.0, "mg/dl": 10.0}},
})
for _cell in ("neutrophils", "lymphocytes", "eosinophils", "monocytes", "basophils"):
    CONVERSION_FACTORS[_cell] = {"canonical": "%", "conversions": PERCENT}
    CONVERSION_FACTORS[f"{_cell}_abs"] = {"canonical": "cells/µL", "conversions": CELLS}

# Canonical spellings, so the canonical unit itself always converts with factor 1.
_CANONICAL_ALIASES = {"cells/ul": "/ul", "million/ul": "10^6/ul", "x10^3/ul": "10^3/ul",
                      "ml/min/1.73m²": "ml/min/1.73m2"}


def clean_unit_string(unit: str) -> str:
    """Normalize unit string: lowercase, remove spaces, unify micro symbol and the many ways labs write cell counts."""
    if not unit:
        return ""
    u = unit.strip().lower()
    u = u.replace(" ", "")
    u = u.replace("μ", "u").replace("µ", "u").replace("×", "x")
    u = re.sub(r"^gms(?=%|/)", "gm", u)  # "gms %", "gms/dL"
    u = u.replace("³", "^3").replace("⁶", "^6").replace("⁹", "^9").replace("¹²", "^12").replace("²", "2")
    u = re.sub(r"/(?:hour|hrs?|h)$", "/hr", u)
    u = re.sub(r"^mm/(?:1st|first)hr$|^mmin(?:the)?(?:1st|first)hr$|^mmat(?:the)?endof(?:1st|first)hr$", "mm/hr", u)
    u = re.sub(r"^ml/min/1\.73(?:sq\.?m|m2|m\^2)$", "ml/min/1.73m2", u)
    if "/" in u and not re.match(r"^[mun]?(?:g|mol|eq|iu|u)/", u):
        top, bottom = u.split("/", 1)
        bottom = re.sub(r"^(?:cu\.?mm|cmm|cumm|mm\^?3|ul|microl(?:itre|iter)?)$", "ul", bottom)
        top = re.sub(r"^x", "", top)
        top = re.sub(r"^10(?:\*\*?|e|\^)?(3|6|9|12)$", r"10^\1", top)
        top = re.sub(r"^(?:cells?|count)$", "", top)
        top = re.sub(r"^(?:lakhs?|lacs?)$", "lakh", top)
        top = re.sub(r"^(?:millions?|mill?|mil\.)$", "10^6", top)
        top = re.sub(r"^(?:thou(?:sands?)?|k|thousand)$", "10^3", top)
        u = f"{top}/{bottom}"
    if re.fullmatch(r"(?:lakhs?|lacs?)", u):
        u = "lakh/ul"  # "2.5 LAKH" in a count row: lakhs per cumm
    return _CANONICAL_ALIASES.get(u, u)

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
