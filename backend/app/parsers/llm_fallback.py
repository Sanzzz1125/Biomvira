import os
import json
import re
from typing import List, Optional, Dict, Any
from app.models.schemas import DetectedBiomarker, ReferenceRange
from app.engine.rule_engine import BIOMARKERS_CONFIG
from app.engine.unit_converter import convert_to_canonical
from app.config import settings

from pydantic import BaseModel
from typing import Literal

class AIResult(BaseModel):
    biomarker_key: Literal["vitamin_d", "vitamin_b12", "folate", "ferritin", "hemoglobin", "calcium"]
    detected_value: float
    detected_unit: str
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None

SYSTEM_PROMPT = """You are an expert diagnostic laboratory data extractor.
Your task is to extract exact biomarker test results from sanitized blood report text.
Target biomarkers:
1. vitamin_d (Vitamin D, 25-OH Vitamin D)
2. vitamin_b12 (Vitamin B12, Cobalamin)
3. folate (Folate, Folic acid, Vitamin B9)
4. ferritin (Serum Ferritin)
5. hemoglobin (Hemoglobin, Hb)
6. calcium (Calcium, Total Calcium)

Return ONLY a raw JSON array of objects without any markdown formatting or code blocks.
Each object must contain:
- biomarker_key: exactly one of: "vitamin_d", "vitamin_b12", "folate", "ferritin", "hemoglobin", "calcium"
- detected_value: float or string containing the number
- detected_unit: string (e.g., "ng/mL", "pg/mL", "g/dL", "mg/dL", "nmol/L", "pmol/L")
- ref_low: float or null
- ref_high: float or null
- confidence: float between 0.0 and 1.0

Do NOT fabricate values. If a biomarker is not mentioned in the text, omit it entirely.
"""

def _resolve_biomarker_key(raw_key: str) -> Optional[str]:
    """Resolves an LLM-provided key or alias to a canonical biomarker key."""
    if not raw_key:
        return None
    cleaned = str(raw_key).strip().lower().replace("-", "_").replace(" ", "_")
    if cleaned in BIOMARKERS_CONFIG:
        return cleaned

    # Check known aliases
    raw_lower = str(raw_key).strip().lower()
    for bio_key, bio_info in BIOMARKERS_CONFIG.items():
        if raw_lower == bio_info.get("display_name", "").lower():
            return bio_key
        for alias in bio_info.get("aliases", []):
            if raw_lower == alias.lower():
                return bio_key

    return None

def _extract_float(val: Any) -> Optional[float]:
    """Safely extracts a float from numeric or string input (e.g. '14.2 ng/mL' -> 14.2)."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        import math
        return float(val) if math.isfinite(val) and not isinstance(val, bool) else None
    match = re.search(r"(\d+(?:\.\d+)?)", str(val))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def parse_llm_json_response(raw_text: str) -> List[DetectedBiomarker]:
    """
    Parses LLM JSON response text safely, handling markdown code fences,
    nested dictionary structures, and malformed numeric fields.
    """
    if not raw_text or not raw_text.strip():
        return []

    cleaned = raw_text.strip()
    # Strip markdown code blocks like ```json ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: search for first [ ... ] or { ... } block
        array_match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if array_match:
            try:
                data = json.loads(array_match.group(0))
            except json.JSONDecodeError:
                return []
        else:
            return []

    # Normalize data into a list of dictionaries
    items: List[Dict[str, Any]] = []
    if isinstance(data, list):
        items = [x for x in data if isinstance(x, dict)]
    elif isinstance(data, dict):
        for candidate_key in ("biomarkers", "detected_biomarkers", "results", "items", "data"):
            if candidate_key in data and isinstance(data[candidate_key], list):
                items = [x for x in data[candidate_key] if isinstance(x, dict)]
                break
        if not items:
            # Check if dict itself represents a single biomarker
            if "biomarker_key" in data or "detected_value" in data:
                items = [data]

    results: List[DetectedBiomarker] = []
    for item in items:
        raw_key = item.get("biomarker_key") or item.get("name") or item.get("key")
        key = _resolve_biomarker_key(raw_key)
        if not key or key not in BIOMARKERS_CONFIG:
            continue

        raw_value = item.get("detected_value", item.get("value"))
        if re.search(r"[<>≤≥]|^\s*-", str(raw_value)):
            continue
        val = _extract_float(raw_value)
        if val is None:
            continue

        raw_unit = str(item.get("detected_unit") or item.get("unit") or "").strip()
        try:
            canonical_val, canonical_unit = convert_to_canonical(key, val, raw_unit)
        except ValueError:
            continue

        ref_low = _extract_float(item.get("ref_low"))
        ref_high = _extract_float(item.get("ref_high"))
        ref_range = ReferenceRange(low=ref_low, high=ref_high) if (ref_low is not None and ref_high is not None) else None

        conf = _extract_float(item.get("confidence"))
        if conf is None or conf <= 0.0 or conf > 1.0:
            conf = 0.90

        results.append(
            DetectedBiomarker(
                biomarker_key=key,
                display_name=BIOMARKERS_CONFIG[key]["display_name"],
                detected_value=val,
                detected_unit=raw_unit,
                canonical_value=canonical_val,
                canonical_unit=canonical_unit,
                report_reference_range=ref_range,
                extraction_method="llm_fallback",
                confidence=None
            )
        )

    return results

def extract_with_gemini_fallback(sanitized_text: str) -> List[DetectedBiomarker]:
    """
    Fallback extraction using Gemini API for ambiguous, noisy, or multi-column layouts.
    Uses settings.gemini_model and settings.gemini_api_key.
    """
    from app.parsers.sanitizer import clinical_evidence_only
    from app.parsers.regex_matcher import extract_biomarkers_with_regex
    evidence = clinical_evidence_only(sanitized_text)
    if not evidence:
        return []
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return []

    try:
        from google import genai
        from google.genai import types

        model_name = settings.gemini_model or "gemini-2.5-flash"
        client = genai.Client(api_key=api_key, http_options={"timeout": settings.gemini_timeout_ms})
        response = client.models.generate_content(
            model=model_name,
            contents=f"{SYSTEM_PROMPT}\n\nReport Text:\n{evidence}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[AIResult]
            )
        )

        if not response or not response.text:
            return []

        candidates = parse_llm_json_response(response.text)
        grounded = extract_biomarkers_with_regex(sanitized_text)
        accepted = []
        for candidate in candidates:
            source = next((m for m in grounded if m.biomarker_key == candidate.biomarker_key
                           and m.canonical_value == candidate.canonical_value
                           and not m.qualifier and not m.warnings), None)
            if source:
                accepted.append(source.model_copy(update={"extraction_method": "llm_fallback"}))
        return accepted
    except Exception:
        raise ValueError("Gemini is unavailable or returned an invalid response.") from None

