"""Bounded local PDF/image extraction. No report images leave this process."""
import io
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import pdfplumber
from PIL import Image, ImageOps, ImageFilter, UnidentifiedImageError
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


def ocr_image(image, deadline):
    if image.width * image.height > settings.max_image_pixels:
        raise ReportError('Image exceeds safe pixel limit.')
    if not shutil.which('tesseract'):
        raise ReportError('OCR is unavailable. Install Tesseract on the server or paste report text.')
    image = ImageOps.exif_transpose(image).convert('RGB')
    gray = ImageOps.autocontrast(ImageOps.grayscale(image)).filter(ImageFilter.SHARPEN)
    if max(gray.size) < 1600:
        scale = min(2, 1600 / max(gray.size))
        gray = gray.resize((int(gray.width * scale), int(gray.height * scale)))
    best = ''
    with tempfile.TemporaryDirectory(prefix='nutrilens-') as directory:
        path = Path(directory) / 'page.png'
        # Bounded orientation trials also handle mobile captures lacking EXIF.
        for angle in (0, 90, 270, 180):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ReportError('Report processing timed out. Try fewer pages.')
            gray.rotate(angle, expand=True).save(path)
            try:
                result = subprocess.run(['tesseract', str(path), 'stdout', '--psm', '6'],
                                        capture_output=True, timeout=min(settings.ocr_timeout_seconds, remaining), check=True)
            except subprocess.TimeoutExpired:
                raise ReportError('OCR timed out. Try a clearer or smaller report.') from None
            except (OSError, subprocess.CalledProcessError):
                raise ReportError('OCR failed. Try a clearer image or paste report text.') from None
            candidate = result.stdout.decode('utf-8', errors='replace')
            from app.parsers.regex_matcher import extract_biomarkers_with_regex
            if len(extract_biomarkers_with_regex(candidate)) > len(extract_biomarkers_with_regex(best)):
                best = candidate
            elif not best and usable(candidate):
                best = candidate
            if extract_biomarkers_with_regex(best):
                break
    if not usable(best):
        raise ReportError('No readable laboratory text found. Upload a clearer report or paste text.')
    return best


def extract_text_and_tables_from_pdf(file_bytes: bytes) -> str:
    deadline = time.monotonic() + settings.processing_timeout_seconds
    chunks = []
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
                    for t in tables)).extract_text() or ''
                text = '\n'.join(rows + [outside])
                from app.parsers.regex_matcher import mentioned_keys, extract_biomarkers_with_regex
                missing = mentioned_keys(text) - {m.biomarker_key for m in extract_biomarkers_with_regex(text)}
                method = 'native'
                if not usable(text) or missing:
                    if page.width * page.height * (180 / 72) ** 2 > settings.max_image_pixels:
                        raise ReportError('PDF page exceeds safe rendering limits.')
                    ocr_text = ocr_image(page.to_image(resolution=180).original, deadline)
                    if not usable(text):
                        text = ocr_text
                        method = 'ocr'
                    else:
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
    return '\n'.join(chunks)


def extract_upload(data, filename, mime):
    if not data:
        raise ReportError('The uploaded file is empty.')
    if len(data) > settings.max_upload_bytes:
        raise ReportError('File exceeds the configured upload size limit.')
    ext = Path(filename or '').suffix.lower()
    expected = {'.pdf': 'application/pdf', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}
    if ext not in expected:
        raise ReportError('Supported formats are PDF, JPG, JPEG and PNG.')
    if mime != expected[ext]:
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
            return '[[PAGE 1 ocr]]\n' + ocr_image(image, time.monotonic() + settings.processing_timeout_seconds)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ReportError('Image is corrupted or exceeds safe limits.') from None
