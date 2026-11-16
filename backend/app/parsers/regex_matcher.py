"""Conservative row parser; uncertain measurements remain reviewable."""
import re
from app.models.schemas import DetectedBiomarker, ReferenceRange
from app.engine.rule_engine import BIOMARKERS_CONFIG
from app.engine.unit_converter import convert_to_canonical

NUMBER = r'\d+(?:[.,]\d+)?'
RANGE_PATTERN = re.compile(r'(' + NUMBER + r')\s*(?:-|–|—|to)\s*(' + NUMBER + r')', re.I)
VALUE = re.compile(r'(?<![\w./])([<>≤≥]=?)?\s*(' + NUMBER + r')(?![\w.])')
UNIT = re.compile(r'\b(?:[munpµμ]?g|gm|gms|mcg|[munpµμ]?mol|meq)\s*/\s*(?:100ml|ml|dl|l|liter|milliliter|mol)\b'
                  r'|\b(?:gm|mg|g)%|\b(?:i?u)\s*/\s*(?:l|ml)\b|(?<![\w%])%', re.I)
# Rows that are ratios or calculated indices are never a single biomarker (e.g. "LDL/HDL", "T.Chol/HDL").
RATIO_ROW = re.compile(r'\b(?:chol|ldl|hdl|vldl|a|tg)\s*/\s*(?:hdl|ldl|chol|g|ratio)\b|\b(?:hdl|ldl|vldl)\s*/', re.I)
# Words that introduce a band description rather than a patient value: "Desirable Level : <200", "Borderline : 200 - 239".
BAND_WORDS = re.compile(r'\b(?:desirable|optimal|near optimal|borderline(?: high)?|undesirable|very high|low risk|average risk|moderate risk|high risk)\b', re.I)


def aliases(line):
    matches = []
    for key, info in BIOMARKERS_CONFIG.items():
        found = [m for alias in info['aliases'] for m in [re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', line, re.I)] if m]
        if found:
            matches.append((key, max(found, key=lambda m: m.end()-m.start())))
    # A name inside a longer name belongs to the longer one ("glycated hemoglobin" is not hemoglobin).
    return [(k, m) for k, m in matches
            if not any(o is not m and (o.start() <= m.start() and o.end() >= m.end()) and (o.end() - o.start()) > (m.end() - m.start())
                       for _, o in matches)]


def mentioned_keys(text):
    """Biomarkers that appear as a test row (name near the start of a line with a number close by).

    Explanatory prose such as "HbA1c is a form of hemoglobin ..." also contains biomarker names but is not
    a result, so a name only counts when it starts a line and either a digit follows within the next two lines or the line is short.
    """
    lines = [l.strip() for l in text.splitlines() if not l.startswith('[[PAGE')]
    keys = set()
    for i, line in enumerate(lines):
        for key, match in aliases(line):
            if match.start() > 30:
                continue
            window = ' '.join(re.sub(r'\([^)]*\)', ' ', l) for l in lines[i:i + 3])
            # A short line that begins with a test name is a row even if its value is missing; a long line is prose.
            if re.search(r'\d', window) or len(line) <= 40:
                keys.add(key)
    return keys


def extract_biomarkers_with_regex(text):
    detected = []
    page = None
    method = 'regex'
    header = None
    pending = ''
    for original in text.splitlines():
        boundary = re.match(r'\[\[PAGE (\d+) (\w+)\]\]', original)
        if boundary:
            page, mode = boundary.groups(); page = int(page)
            method = 'ocr_regex' if mode == 'ocr' else 'regex'
            header = None; pending = ''; continue
        line = original.strip()
        cells = [s.strip() for s in re.split(r'\s*\|\s*|\t+|\s{2,}', line)]
        if any(re.fullmatch(r'(?:current\s+)?result|value', c, re.I) for c in cells) and any(re.search('test|parameter|investigation', c, re.I) for c in cells):
            header = [c.lower() for c in cells]; continue
        if RATIO_ROW.search(line):
            pending = ''
            continue
        hits = aliases(line)
        if not hits and pending:
            line = pending + ' ' + line; hits = aliases(line); pending = ''
        if len(hits) != 1:
            continue
        key, match = hits[0]
        rest = line[match.end():]
        rest = re.sub(r'\([^)]*\)', ' ', rest)
        rest = re.sub(r'\b(?:25\s*[-–]?\s*(?:oh|hydroxy)\w*|vit\s*b9|d3)\b', ' ', rest, flags=re.I)
        band = BAND_WORDS.search(rest)
        if band:
            # Multi-band reference text (lipids): the patient's value is whatever comes before the first band word,
            # and no single reference range can be read from it.
            rest = rest[:band.start()]
        ref = RANGE_PATTERN.search(rest)
        search = rest[:ref.start()] if ref else rest
        warnings = []
        if header and len(cells) == len(header):
            result_columns = [i for i,c in enumerate(header) if re.fullmatch(r'(?:current\s+)?result|value', c)]
            if len(result_columns) == 1:
                search = cells[result_columns[0]]
                unit_columns = [i for i,c in enumerate(header) if c in ('unit','units')]
                if unit_columns:
                    search += ' ' + cells[unit_columns[0]]
                range_columns = [i for i,c in enumerate(header) if 'reference' in c or 'range' in c]
                ref = RANGE_PATTERN.search(cells[range_columns[0]]) if range_columns else None
        # Mask units before searching: g/100ml must not supply a patient value.
        numbers = list(VALUE.finditer(UNIT.sub(lambda m: ' ' * len(m.group()), search)))
        if len(numbers) > 1 and not numbers[0].group(1):
            # "14 U/L < 50 U/L": a later "<50" or ">60" is the reference limit, not a second result.
            numbers = [numbers[0]] + [n for n in numbers[1:] if not n.group(1)]
        if not numbers:
            if not re.search(r'\d', rest) and len(line) < 100:
                pending = line
            continue
        if len(numbers) != 1 or re.search(r'previous|historical|prior', line, re.I):
            warnings.append('Ambiguous or historical result; verify against current report.')
        target = numbers[0]
        if search[:target.start()].rstrip().endswith("-"):
            continue
        value = float(target.group(2).replace(',', '.'))
        qualifier = target.group(1)
        unit_match = UNIT.search(search)
        unit = unit_match.group() if unit_match else ''
        if not unit:
            # Preserve explicit unknown units, never supply a canonical default.
            suffix = search[target.end():].strip(' :|*')
            unit = suffix.split()[0] if suffix and suffix.split()[0].lower() not in ('h','l','high','low') else ''
        try:
            canonical, canonical_unit = convert_to_canonical(key, value, unit)
        except ValueError:
            canonical, canonical_unit = None, BIOMARKERS_CONFIG[key]['canonical_unit']
            warnings.append('Missing or unsupported unit; correct before analysis.')
        if qualifier:
            warnings.append('Qualified result is a bound, not an exact measurement; cannot analyze as exact.')
        if method == 'ocr_regex':
            warnings.append('OCR transcription requires comparison with the original image.')
        flag = re.search(r'(?:^|\s|\|)(H|L|High|Low|\*+)(?=\s|\||$)(?!\s*:)', rest, re.I)
        marker = DetectedBiomarker(
            biomarker_key=key, display_name=BIOMARKERS_CONFIG[key]['display_name'],
            detected_value=value, detected_unit=unit, canonical_value=canonical, canonical_unit=canonical_unit,
            report_reference_range=ReferenceRange(low=float(ref[1].replace(',', '.')), high=float(ref[2].replace(',', '.'))) if ref else None,
            extraction_method=method, source_page=page, source_text=line, qualifier=qualifier,
            abnormal_flag=flag[1] if flag else None, warnings=warnings)
        equivalent = next((m for m in detected if m.biomarker_key == key and m.detected_value == value and m.detected_unit.lower() == unit.lower() and m.qualifier == qualifier and m.warnings == warnings), None)
        if not equivalent:
            detected.append(marker)
    for marker in detected:
        if sum(m.biomarker_key == marker.biomarker_key for m in detected) > 1:
            marker.verification_status = 'conflict'
            marker.warnings.append('Conflicting/repeated measurements: select the current result and remove others.')
    return detected
