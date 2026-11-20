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
    biomarker_key: str
    detected_value: float
    detected_unit: str
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None


SYSTEM_PROMPT = """You read laboratory test rows that a rule-based reader could not parse.
Each input line starts with a test key, followed by the numbers, units and range tokens from that row of the report
(everything else on the row was removed for privacy).
For each line, return the result value, its unit and the reference range if one is printed.
Return ONLY a JSON array of objects with: biomarker_key (exactly the key given at the start of the line),
detected_value (number), detected_unit (string, as printed), ref_low (number or null), ref_high (number or null).
Never invent a number: use only numbers present on that line. If the value is not clear, leave that test out.
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

_NUMBER = re.compile(r"^[<>≤≥]?\d+(?:[.,]\d+)*$")
_RANGE_WORDS = {"-", "–", "—", "to", "<", ">", "≤", "≥", "upto", "up"}


def _units() -> set:
    units = {"%", "fl", "pg", "iu", "mm/hr", "lakh", "lakhs", "million", "thousand", "cells/cumm", "/cumm", "x10^3/ul"}
    for cfg in BIOMARKERS_CONFIG.values():
        for unit in [cfg.get("canonical_unit", "")] + list(cfg.get("alternate_units", [])):
            if unit:
                units.add(unit.lower())
    return units


def missed_rows(sanitized_text: str, keys: set) -> Dict[str, str]:
    """For each test named on a row whose value the rules could not read: that row (and the next lines up to the
    next test) reduced to clinical tokens only - numbers, units and range words. Names, addresses and any other words
    are dropped, so nothing personal can reach the AI helper."""
    from app.parsers.regex_matcher import aliases
    units = _units()
    lines = [l.strip() for l in sanitized_text.splitlines() if l.strip() and not l.startswith("[[PAGE")]
    rows: Dict[str, str] = {}
    for i, line in enumerate(lines):
        for key, match in aliases(line):
            if key not in keys or key in rows or match.start() > 30:
                continue
            window = [line[match.end():]]
            for nxt in lines[i + 1:i + 3]:
                if aliases(nxt):
                    break  # the next test's row
                window.append(nxt)
            tokens = []
            for token in re.split(r"\s+", " ".join(window).replace("(", " ").replace(")", " ")):
                t = token.strip(":;,")
                if _NUMBER.match(t) or t.lower() in units or t.lower() in _RANGE_WORDS:
                    tokens.append(t)
            if any(_NUMBER.match(t) for t in tokens):
                rows[key] = f"{key}: {' '.join(tokens)}"
    return rows


def _numbers(row: str) -> set:
    return {float(t.lstrip("<>≤≥").replace(",", "")) for t in row.split() if _NUMBER.match(t)}


def extract_with_gemini_fallback(sanitized_text: str, missing: Optional[set] = None) -> List[DetectedBiomarker]:
    """Ask Gemini to read rows the rules missed (tests named on the report whose value could not be read).

    Gemini sees only those rows, reduced to clinical tokens. A value is kept only if it is a number printed on that
    test's own row and its unit is recognised; it is always marked for the person to check before analysis.
    """
    from app.parsers.regex_matcher import extract_biomarkers_with_regex, found_keys, mentioned_keys
    if missing is None:
        missing = mentioned_keys(sanitized_text) - found_keys(extract_biomarkers_with_regex(sanitized_text))
    rows = missed_rows(sanitized_text, set(missing))
    if not rows:
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
            contents=f"{SYSTEM_PROMPT}\n\nRows:\n" + "\n".join(rows.values()),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[AIResult]
            )
        )
        if not response or not response.text:
            return []
        accepted = []
        for candidate in parse_llm_json_response(response.text):
            row = rows.get(candidate.biomarker_key)
            if row is None or candidate.detected_value not in _numbers(row):
                continue  # only tests we asked about, and only numbers printed on their own row
            if candidate.detected_unit.lower() not in {t.lower() for t in row.split()}:
                continue  # the unit must be printed on the row too
            rng = candidate.report_reference_range
            if rng and not ({rng.low, rng.high} <= _numbers(row)):
                rng = None
            if any(m.biomarker_key == candidate.biomarker_key for m in accepted):
                continue
            accepted.append(candidate.model_copy(update={
                "report_reference_range": rng, "extraction_method": "llm_fallback", "verification_status": "needs_review",
                "warnings": ["Read by the AI helper from a row the rules could not read. Check it against your report."]}))
        return accepted
    except Exception:
        raise ValueError("Gemini is unavailable or returned an invalid response.") from None
