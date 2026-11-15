import re
from typing import Tuple

# Regex patterns for identifying personal health information in Indian diagnostic reports
# Note: Use horizontal whitespace ([A-Za-z\.\t ]) with lookaheads so newlines and subsequent fields are never consumed
PII_PATTERNS = [
    # Patient name lines (stops at pipe delimiter, subsequent fields, or newline)
    (r"(?i)(patient\s*name|name\s*of\s*patient|pt\s*name|client\s*name)\s*[:\-]\s*([A-Za-z\.\t ]+?)(?=\s*(?:\||age|sex|gender|dob|ref|doctor|dr\.|uhid|date|bill|\b\d)|\n|$)", r"\1: [REDACTED_NAME]"),
    # Referring doctor lines
    (r"(?i)(ref\s*by|referred\s*by|ref\s*doctor|doctor)\s*[:\-]\s*([^\n|]+?)(?=\s*(?:\||contact|phone|mobile|date|clinic|hospital|qual|reg|uhid|\b\d)|\n|$)", r"\1: [REDACTED_DOCTOR]"),
    # Phone / Mobile numbers (Indian 10-digit formats with optional +91 or 0)
    (r"(?:\+91[\-\s]?)?[6-9]\d{9}", "[REDACTED_PHONE]"),
    # Email addresses
    (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]"),
    # Lab IDs, UHID, Barcodes, Sample numbers
    (r"(?i)(uhid|pid|reg\s*no|sample\s*id|barcode|accession\s*no|bill\s*no)\s*[:\-]\s*([A-Za-z0-9\-_]+)", r"\1: [REDACTED_ID]")
]

def sanitize_report_text(raw_text: str) -> Tuple[str, bool]:
    """
    Scrubs patient identifying details from text before sending to LLMs or public logs.
    Returns (sanitized_text, was_redacted).
    """
    if not raw_text:
        return "", False

    sanitized = raw_text
    modified = False

    for pattern, replacement in PII_PATTERNS:
        new_text, count = re.subn(pattern, replacement, sanitized)
        if count > 0:
            sanitized = new_text
            modified = True

    return sanitized, modified



def clinical_evidence_only(text: str) -> str:
    """Fail-closed allowlist: transmit parsed clinical tokens, never free-form rows.

    Regex redaction alone cannot verify arbitrary medical text is de-identified.
    Unsupported/ambiguous layouts therefore stay local for manual review.
    """
    from app.parsers.regex_matcher import extract_biomarkers_with_regex
    rows = []
    for marker in extract_biomarkers_with_regex(text):
        if marker.canonical_value is None or marker.warnings:
            continue
        row = f'{marker.biomarker_key}: {marker.detected_value} {marker.detected_unit}'
        if marker.report_reference_range:
            row += f' reference {marker.report_reference_range.low}-{marker.report_reference_range.high}'
        rows.append(row)
    return '\n'.join(rows)
