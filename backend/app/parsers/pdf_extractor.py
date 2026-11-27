"""Bounded local PDF/image extraction. No report images leave this process."""
import io
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import pdfplumber
from PIL import Image, ImageChops, ImageFilter, ImageOps, UnidentifiedImageError
from app.config import settings


class ReportError(ValueError):
    pass


def usable(text):
    from app.parsers.regex_matcher import UNIT, RANGE_PATTERN
    # Length alone admits headers and corrupt font maps. Require clinical-looking rows.
    return (len(text.strip()) >= 8 and bool(re.search(r'\d', text))
            and bool(re.search(r'[A-Za-z]{2}', text))
            and bool(UNIT.search(text) or RANGE_PATTERN.search(text))
            and sum(c == '\ufffd' or (ord(c) < 32 and c not in '\n\t') for c in text) / max(len(text), 1) < .02)


OCR_SIDE = 2600  # long side of the page given to Tesseract: big photos shrink, small ones grow
PDF_MARGIN_SECONDS = 20      # the worker process starts up and parses results inside the same time limit
NATIVE_RESERVE_SECONDS = 10  # kept free after OCR so the text layer of the remaining pages is always read
# A lone ":" that OCR read as "2", "3", "i", "L" or "+" between a test name and its value ("Total RBC Count 2 3.91",
# "Basophils L 0 %"). Not touched when the next number starts a range ("Eosinophils 3 1 - 6"), so a real single-digit
# result is never removed.
COLON_READ_AS_DIGIT = re.compile(r'^(\s*[A-Za-z][^\d\n]{2,60}?)\s+[23:;|!iIlL+]\s+(?=\d[\d,]*(?:\.\d+)?(?![\d.,])(?!\s*[-–]\s*\d))',
                                 re.M)
# A range dash that OCR read as "=" ("Normal : 40= 75%"). Lab rows never put "=" between two numbers.
DASH_READ_AS_EQUALS = re.compile(r'(?<=\d)\s*=\s*(?=\d)')
# The "/" of "/Cumm" read as "{", "|", "(", "[", "i", "l" or "!" ("8,400 {Cumm", "LAKH icumm").
SLASH_BEFORE_CUMM = re.compile(r'(?<=[\s\d])[{|(\[iIl!]\s?(?=c(?:u\.?\s*)?mm\b)', re.I)


# Zeros of a range read as letters ("Normal : QO - 02%"): a lone token of only 0/O/o/Q right beside a range dash.
ZEROS_READ_AS_LETTERS = re.compile(r'(?<![\w.])(?=[0OoQ]{0,2}[OoQ])[0OoQ]{1,3}(?=\s*[-–]\s*\d)'
                                   r'|(?<=\d)(\s*[-–]\s*)(?=[0OoQ]{0,2}[OoQ])[0OoQ]{1,3}(?![\w.])')


def _zeros(match):
    return (match.group(1) or '') + '0' * len(match.group().replace(match.group(1) or '', '', 1))


def fix_ocr_text(raw):
    """Repairs OCR's usual misreadings of lab-report punctuation; real digits are never changed."""
    text = COLON_READ_AS_DIGIT.sub(r'\1 : ', raw)
    text = DASH_READ_AS_EQUALS.sub(' - ', text)
    text = ZEROS_READ_AS_LETTERS.sub(_zeros, text)
    return SLASH_BEFORE_CUMM.sub('/', text)


def _otsu(gray):
    hist = gray.histogram(); total = sum(hist); weighted = sum(i * hist[i] for i in range(256))
    w_back = s_back = 0; best, threshold = 0.0, 128
    for t in range(256):
        w_back += hist[t]
        if 0 < w_back < total:
            s_back += t * hist[t]
            m_back, m_fore = s_back / w_back, (weighted - s_back) / (total - w_back)
            between = w_back * (total - w_back) * (m_back - m_fore) ** 2
            if between > best:
                best, threshold = between, t
    return threshold


def flatten_for_ocr(image):
    """Upright (EXIF), grey, resized to OCR_SIDE, and uneven lighting and shadows removed (the page minus a blurred
    copy of itself)."""
    gray = ImageOps.exif_transpose(image).convert('L')
    scale = OCR_SIDE / max(gray.size)
    gray = gray.resize((max(1, round(gray.width * scale)), max(1, round(gray.height * scale))), Image.LANCZOS)
    background = gray.filter(ImageFilter.GaussianBlur(max(9, OCR_SIDE // 100)))
    return ImageOps.autocontrast(ImageOps.invert(ImageChops.subtract(background, gray)))


def prepare_for_ocr(image, flat=None):
    """A phone photo or scanned page as clean black text on white: the flattened page in black/white (Otsu)."""
    flat = flat if flat is not None else flatten_for_ocr(image)
    threshold = _otsu(flat)
    return flat.point(lambda p: 255 if p > threshold else 0)


def _tesseract(img, path, env, timeout):
    img.save(path)
    result = subprocess.run(['tesseract', str(path), 'stdout', '--psm', '6'], env=env,
                            capture_output=True, timeout=timeout, check=True)
    return result.stdout.decode('utf-8', errors='replace')


def _unsure_tests(raw, fixed, flat, angle, path, env, deadline):
    """Which tests a person should check. The page is read a second time from the grey (not black/white) image;
    a row is sure only when both readings agree on its value (and on its printed range, when both found one) and the
    ':' correction did not change its value. If the second reading cannot be made, every value is treated as unsure."""
    from app.parsers.regex_matcher import extract_biomarkers_with_regex as read

    def rows(text):
        return {m.biomarker_key: (m.detected_value, m.report_reference_range) for m in read(text)}

    main = rows(fixed)
    before = rows(raw)
    unsure = {k for k, (v, _) in main.items() if k not in before or before[k][0] != v}
    remaining = deadline - time.monotonic()
    try:
        if remaining < 3:
            raise subprocess.TimeoutExpired('tesseract', 0)
        second = fix_ocr_text(_tesseract(flat.rotate(angle, expand=True), path, env,
                                         min(settings.ocr_timeout_seconds, remaining)))
    except (subprocess.TimeoutExpired, OSError, subprocess.CalledProcessError):
        return set(main)
    other = rows(second)
    for k, (value, ref) in main.items():
        if k not in other or other[k][0] != value or (ref and other[k][1] and ref != other[k][1]):
            unsure.add(k)
    return unsure


def ocr_image(image, deadline, angles=(0, 90, 270, 180)):
    if image.width * image.height > settings.max_image_pixels:
        raise ReportError('Image exceeds safe pixel limit.')
    if not shutil.which('tesseract'):
        raise ReportError('OCR is unavailable. Install Tesseract on the server or paste report text.')
    flat = flatten_for_ocr(image)
    gray = prepare_for_ocr(image, flat)
    # One thread: on a small shared server, Tesseract's default threading makes it many times slower.
    env = {**os.environ, 'OMP_THREAD_LIMIT': '1'}
    best = best_raw = ''
    best_angle = 0
    with tempfile.TemporaryDirectory(prefix='biomvira-') as directory:
        path = Path(directory) / 'page.png'
        # Bounded orientation trials also handle mobile captures lacking EXIF.
        for angle in angles:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ReportError('Report processing timed out. Try fewer pages.')
            gray.rotate(angle, expand=True).save(path)
            try:
                result = subprocess.run(['tesseract', str(path), 'stdout', '--psm', '6'], env=env,
                                        capture_output=True, timeout=min(settings.ocr_timeout_seconds, remaining), check=True)
            except subprocess.TimeoutExpired:
                raise ReportError('OCR timed out. Try a clearer or smaller report.') from None
            except (OSError, subprocess.CalledProcessError):
                raise ReportError('OCR failed. Try a clearer image or paste report text.') from None
            raw = result.stdout.decode('utf-8', errors='replace')
            candidate = fix_ocr_text(raw)
            from app.parsers.regex_matcher import extract_biomarkers_with_regex
            if len(extract_biomarkers_with_regex(candidate)) > len(extract_biomarkers_with_regex(best)):
                best, best_raw, best_angle = candidate, raw, angle
            elif not best and usable(candidate):
                best, best_raw, best_angle = candidate, raw, angle
            if extract_biomarkers_with_regex(best):
                break
        if not usable(best):
            raise ReportError('No readable laboratory text found. Upload a clearer report or paste text.')
        unsure = _unsure_tests(best_raw, best, flat, best_angle, path, env, deadline)
    # Values both readings agree on go straight through; only these are shown for the person to check.
    return best + (f"\n[[UNSURE {','.join(sorted(unsure))}]]" if unsure else '')


def extract_text_and_tables_from_pdf(file_bytes: bytes) -> str:
    # Finish well inside the worker's own time limit (it also has to start up), and stop OCR earlier still: reading
    # the text layer of the remaining pages is fast, so OCR on one page must never cost the whole report.
    deadline = time.monotonic() + settings.processing_timeout_seconds - PDF_MARGIN_SECONDS
    ocr_deadline = deadline - NATIVE_RESERVE_SECONDS
    chunks = []
    failed = None  # OCR error from a picture-only page, raised only if no page was readable
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages or len(pdf.pages) > settings.max_report_pages:
                raise ReportError('PDF is empty or exceeds the configured page limit.')
            for index, page in enumerate(pdf.pages, 1):
                if time.monotonic() > deadline:
                    raise ReportError('Report processing timed out.')
                tables = page.find_tables()
                rows = [' | '.join((cell or '').replace('\n', ' ').strip() for cell in row)
                        for table in tables for row in table.extract() if row]
                # Exclude table bounding boxes from plain text to avoid duplicate representations.
                outside = page.filter(lambda obj: not any(
                    obj.get('x0', 0) >= t.bbox[0] and obj.get('x1', 0) <= t.bbox[2]
                    and obj.get('top', 0) >= t.bbox[1] and obj.get('bottom', 0) <= t.bbox[3]
                    for t in tables)).extract_text(y_tolerance=5) or ''  # some labs print the value a few points above its name
                text = '\n'.join(rows + [outside])
                from app.parsers.regex_matcher import mentioned_keys, extract_biomarkers_with_regex, found_keys
                missing = mentioned_keys(text) - found_keys(extract_biomarkers_with_regex(text))
                method = 'native'
                # OCR is slow (especially on small servers), so it runs only for pages that look like images:
                # a page with almost no text, or a page with an embedded image whose text is unusable or seems to be
                # missing a biomarker row. A text-only page (e.g. a continuation page of explanatory prose) is never
                # OCRed. If OCR fails on a page that already has text, the text is kept instead of failing the report.
                blank = len(text.strip()) < 40 and not usable(text)
                # Logos, QR codes and signatures are small; only a page that is largely a picture (a scan or an
                # analyser printout) can hold results that the text layer is missing.
                covered = sum(max(0, min(i['x1'], page.width) - max(i['x0'], 0)) * max(0, min(i['bottom'], page.height) - max(i['top'], 0))
                              for i in page.images) / max(page.width * page.height, 1)
                # A letterhead or background picture behind a page with no test on it (a signature or notes page) in a
                # report whose earlier pages were readable holds no results; OCR there only costs time.
                notes_page = not blank and not missing and not mentioned_keys(text) and any(usable(c) for c in chunks)
                # A picture behind the whole page with readable text and several results on top is a letterhead
                # background, not a scan: test names in its explanation paragraphs must not trigger OCR of the page.
                background = covered >= 0.95 and usable(text) and len(extract_biomarkers_with_regex(text)) >= 3
                if (blank or (covered >= 0.3 and (not usable(text) or missing))) and not notes_page and not background:
                    ocr_text = ''
                    if time.monotonic() > ocr_deadline:
                        if blank:
                            failed = ReportError('Report processing timed out. Try fewer pages or paste text.')
                    elif page.width * page.height * (180 / 72) ** 2 > settings.max_image_pixels:
                        if blank:
                            failed = ReportError('PDF page exceeds safe rendering limits.')
                    else:
                        try:
                            # A PDF page is already upright, so only phone photos need the rotation trials.
                            ocr_text = ocr_image(page.to_image(resolution=180).original, ocr_deadline, angles=(0,))
                        except ReportError as exc:
                            if blank:
                                failed = exc
                    if blank and not ocr_text:
                        # One unreadable picture page (e.g. an analyser printout) must not sink a report whose other
                        # pages are readable; it is flagged for the user instead.
                        chunks.append(f'[[PAGE {index} unread]]')
                        continue
                    if ocr_text and not usable(text):
                        text = ocr_text
                        method = 'ocr'
                    elif ocr_text:
                        # Keep native evidence and add only new OCR measurements.
                        native_markers = extract_biomarkers_with_regex(text)
                        additions = [m.source_text for m in extract_biomarkers_with_regex(ocr_text)
                                     if not any(n.biomarker_key == m.biomarker_key and n.canonical_value == m.canonical_value
                                                for n in native_markers)]
                        if additions:
                            text += f'\n[[PAGE {index} ocr]]\n' + '\n'.join(additions)
                chunks.append(f'[[PAGE {index} {method}]]\n{text}')
                if sum(map(len, chunks)) > settings.max_text_chars:
                    raise ReportError('Extracted report exceeds text limit.')
    except ReportError:
        raise
    except Exception as exc:
        from pdfminer.pdfdocument import PDFPasswordIncorrect
        if isinstance(exc, PDFPasswordIncorrect) or isinstance(exc.__context__, PDFPasswordIncorrect):
            raise ReportError('Password-protected PDFs are not supported. Upload an unlocked copy.') from None
        raise ReportError('PDF is corrupted or cannot be read.') from None
    if failed and not any(usable(chunk) for chunk in chunks):
        raise failed
    return '\n'.join(chunks)


def extract_upload(data, filename, mime):
    if not data:
        raise ReportError('The uploaded file is empty.')
    if len(data) > settings.max_upload_bytes:
        raise ReportError('File exceeds the configured upload size limit.')
    ext = Path(filename or '').suffix.lower()
    expected = {'.pdf': {'application/pdf'}, '.jpg': {'image/jpeg', 'image/jpg', 'image/pjpeg'},
                '.jpeg': {'image/jpeg', 'image/jpg', 'image/pjpeg'}, '.png': {'image/png'}}
    if ext not in expected:
        raise ReportError('Supported formats are PDF, JPG, JPEG and PNG.')
    if mime not in expected[ext]:
        raise ReportError('File MIME type does not match its extension.')
    if ext == '.pdf':
        if not data.startswith(b'%PDF-'):
            raise ReportError('File content is not a PDF.')
        return extract_text_and_tables_from_pdf(data)
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != ('PNG' if ext == '.png' else 'JPEG'):
                raise ReportError('Image content does not match its extension.')
            if image.width * image.height > settings.max_image_pixels:
                raise ReportError('Image exceeds safe pixel limit.')
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            if image.format == 'JPEG':
                # JPEG can decode at 1/2, 1/4 or 1/8 size for free; ask for the smallest that still covers OCR_SIDE,
                # so a 48 MP photo is decoded at about 12 MP (a quarter of the memory).
                image.draft('L', (OCR_SIDE, OCR_SIDE))
            return '[[PAGE 1 ocr]]\n' + ocr_image(image, time.monotonic() + settings.processing_timeout_seconds)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ReportError('Image is corrupted or exceeds safe limits.') from None
