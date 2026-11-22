"""Phone photos of reports: size and type checks, cleanup before OCR, single-thread Tesseract, and the ':'-read-as-digit
fix. Images are drawn from made-up text; no real report is used."""
import io
import shutil

import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.engine.unit_converter import convert_to_canonical
from app.parsers import pdf_extractor as pdf
from app.parsers.regex_matcher import extract_biomarkers_with_regex

ROWS = ["Investigation        Result     Unit        Normal Range", "Haemoglobin    :   10.2   gms %   12.0 - 15.0",
        "Total RBC Count   :   3.91   millions/Cumm   3.9 - 6.5", "Total W B C Count  :  8,400  /Cumm  4,000 - 11,000",
        "Neutrophils    :   81  %    40 - 75%", "Lymphocytes    :   14  %    20 - 45%"]


def photo(width, height, quality=85):
    """A tilted, shadowed, slightly blurred photo of a made-up report on a desk, as JPEG bytes."""
    page = Image.new("L", (1240, 1754), 255)
    draw = ImageDraw.Draw(page)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 30)
    except OSError:
        font = ImageFont.load_default(size=30)
    for i, row in enumerate(ROWS):
        draw.text((80, 150 + i * 70), row, fill=0, font=font)
    page = page.rotate(-2, expand=True, fillcolor=255)
    shade = Image.linear_gradient("L").resize(page.size).point(lambda p: 255 - p // 3)  # light falling off
    page = Image.composite(page, Image.new("L", page.size, 0), shade)
    desk = Image.new("L", (page.width + 120, page.height + 120), 110)
    desk.paste(page, (60, 60))
    out = io.BytesIO()
    desk.filter(ImageFilter.GaussianBlur(0.8)).resize((width, height)).convert("RGB").save(out, "JPEG", quality=quality)
    return out.getvalue()


def test_cleanup_gives_black_text_on_white_at_reading_size():
    img = pdf.prepare_for_ocr(Image.open(io.BytesIO(photo(900, 1200))))
    assert max(img.size) == pdf.OCR_SIDE and set(img.getdata()) <= {0, 255}


@pytest.mark.parametrize("line,expected", [
    ("Total RBC Count 2 3.91 millions/Cumm 3.9 - 6.5", "Total RBC Count : 3.91 millions/Cumm 3.9 - 6.5"),
    ("platelet Count 3 2,53,000 LAKH /Cumm 1.5 - 4.0", "platelet Count : 2,53,000 LAKH /Cumm 1.5 - 4.0"),
    ("Eosinophils 3 1 - 6 %", "Eosinophils 3 1 - 6 %"),   # a real value followed by its range is kept
    ("Basophils 0 %", "Basophils 0 %"),
    ("Monocytes 2 %  Normal 1 - 6%", "Monocytes 2 %  Normal 1 - 6%"),
])
def test_colon_read_as_digit(line, expected):
    assert pdf.COLON_READ_AS_DIGIT.sub(r"\1 : ", line) == expected


def test_bare_lakh_is_a_platelet_unit():
    assert convert_to_canonical("platelets", 2.53, "LAKH") == (253.0, "×10³/µL")


@pytest.mark.parametrize("mime", ["image/jpeg", "image/jpg", "image/pjpeg"])
def test_phone_jpeg_mime_variants_are_accepted(monkeypatch, mime):
    monkeypatch.setattr(pdf, "ocr_image", lambda image, deadline: "Haemoglobin 10.2 g/dL")
    assert "Haemoglobin" in pdf.extract_upload(photo(600, 800), "photo.jpg", mime)


def test_tesseract_runs_single_threaded(monkeypatch):
    seen = {}
    monkeypatch.setattr(pdf.shutil, "which", lambda _: "/fake/tesseract")

    def fake_run(cmd, **kwargs):
        seen.update(kwargs.get("env") or {})
        raise pdf.subprocess.CalledProcessError(1, cmd)
    monkeypatch.setattr(pdf.subprocess, "run", fake_run)
    with pytest.raises(pdf.ReportError):
        pdf.ocr_image(Image.new("L", (400, 600), 255), pdf.time.monotonic() + 30)
    assert seen.get("OMP_THREAD_LIMIT") == "1"


@pytest.mark.skipif(not shutil.which("tesseract"), reason="Tesseract not installed")
@pytest.mark.parametrize("size", [(900, 1200), (6000, 8000)])   # a WhatsApp-sized photo and a 48 MP camera photo
def test_phone_photos_are_read(size):
    text = pdf.extract_upload(photo(*size), "photo.jpg", "image/jpeg")
    got = {m.biomarker_key: m.detected_value for m in extract_biomarkers_with_regex(text)}
    assert got.get("hemoglobin") == 10.2 and got.get("rbc") == 3.91 and got.get("neutrophils") == 81


@pytest.mark.skipif(not shutil.which("tesseract"), reason="Tesseract not installed")
def test_clear_photo_values_need_no_confirmation():
    from app.api.v1.extract import process_report
    result = process_report(photo(900, 1200), "photo.jpg", "image/jpeg", None)
    assert result.extracted_biomarkers
    assert not [m.biomarker_key for m in result.extracted_biomarkers if any(w.startswith("OCR transcription") for w in m.warnings)]


def test_only_disagreeing_or_corrected_values_are_flagged(monkeypatch):
    main_raw = "Haemoglobin : 10.2 g/dL\nTotal RBC Count 2 3.91 millions/cumm\nVitamin D : 18 ng/mL"
    fixed = pdf.COLON_READ_AS_DIGIT.sub(r"\1 : ", main_raw)
    second = "Haemoglobin : 10.2 g/dL\nTotal RBC Count : 3.91 millions/cumm\nVitamin D : 13 ng/mL"
    monkeypatch.setattr(pdf, "_tesseract", lambda *a, **k: second)
    unsure = pdf._unsure_tests(main_raw, fixed, Image.new("L", (10, 10)), 0, "x.png", {}, pdf.time.monotonic() + 30)
    assert unsure == {"rbc", "vitamin_d"}   # rbc: ':' corrected; vitamin D: readings disagree; haemoglobin: sure


def test_second_reading_failure_flags_everything(monkeypatch):
    def fail(*a, **k):
        raise pdf.subprocess.TimeoutExpired("tesseract", 1)
    monkeypatch.setattr(pdf, "_tesseract", fail)
    text = "Haemoglobin : 10.2 g/dL\nVitamin D : 18 ng/mL"
    assert pdf._unsure_tests(text, text, Image.new("L", (10, 10)), 0, "x.png", {}, pdf.time.monotonic() + 30) == {"hemoglobin", "vitamin_d"}


def test_unsure_marker_controls_the_review_warning():
    from app.parsers.regex_matcher import extract_biomarkers_with_regex
    text = "[[PAGE 1 ocr]]\nHaemoglobin : 10.2 g/dL\nVitamin D : 18 ng/mL\n[[UNSURE vitamin_d]]"
    flagged = {m.biomarker_key for m in extract_biomarkers_with_regex(text) if any(w.startswith("OCR transcription") for w in m.warnings)}
    assert flagged == {"vitamin_d"}


@pytest.mark.parametrize("line,expected", [
    ("Basophils L 0 % Normal : 00 - 02%", "Basophils : 0 % Normal : 00 - 02%"),      # ':' read as L
    ("Eosinophils i 3 % Normal : 02 - 06", "Eosinophils : 3 % Normal : 02 - 06"),    # ':' read as i
    ("Neutrophils + 81 % Normal: 40= 75%", "Neutrophils : 81 % Normal: 40 - 75%"),   # ':' as +, '-' as '='
    ("Total WBC Count : 8,400 {Cumm 4,000 - 11,000", "Total WBC Count : 8,400 /Cumm 4,000 - 11,000"),
    ("platelet Count : 2,53,000 LAKH icumm 1.5 - 4.0", "platelet Count : 2,53,000 LAKH /cumm 1.5 - 4.0"),
    ("Haemoglobin : 10.2 gms % 12.5 - 18.0", "Haemoglobin : 10.2 gms % 12.5 - 18.0"),  # clean rows unchanged
    ("Basophils : 0 % Normal : QO - 02%", "Basophils : 0 % Normal : 00 - 02%"),       # zeros read as letters
    ("Basophils : 0 % Normal : 00 - O2%", "Basophils : 0 % Normal : 00 - O2%"),       # not a lone token: kept
    ("Basophils : 0 % Normal : 0 - O", "Basophils : 0 % Normal : 0 - 0"),
    ("Vitamin D : 18 ng/mL NO - 2 tablets", "Vitamin D : 18 ng/mL NO - 2 tablets"),    # words never touched
])
def test_fix_ocr_text(line, expected):
    assert pdf.fix_ocr_text(line) == expected


def test_photo_rows_with_misread_punctuation_parse_fully():
    text = pdf.fix_ocr_text("Total WBC Count : 8,400 {Cumm 4.000 - 11,000/Cum'\n"
                            "Neutrophils + 81 % Normal: 40= 75%\nLymphocytes i 14 % Normal : 20= 45%\n"
                            "Basophils L 0 % Normal : 00 - 02%")
    rows = {m.biomarker_key: m for m in extract_biomarkers_with_regex(text)}
    wbc = rows["wbc"]
    assert (wbc.detected_value, wbc.canonical_unit) == (8400, "cells/µL") and not wbc.warnings
    assert (wbc.report_reference_range.low, wbc.report_reference_range.high) == (4000, 11000)
    for key, low, high in (("neutrophils", 40, 75), ("lymphocytes", 20, 45), ("basophils", 0, 2)):
        assert (rows[key].report_reference_range.low, rows[key].report_reference_range.high) == (low, high)
        assert not rows[key].warnings and rows[key].abnormal_flag is None


@pytest.mark.parametrize("range_text,expected", [
    ("4.000 - 11,000", (4000, 11000)),   # thousands comma read as a dot
    ("4.0 - 11.0", (4.0, 11.0)),
    ("4.000 - 11.000", (4.0, 11.0)),     # both ends alike: kept as printed
    ("1.5 - 4.0", (1.5, 4.0)),
])
def test_range_thousands_dot(range_text, expected):
    from app.parsers.regex_matcher import RANGE_PATTERN, read_range
    assert read_range(RANGE_PATTERN.search(range_text)) == expected


def test_disagreeing_ranges_are_flagged(monkeypatch):
    main = "Neutrophils : 81 % 40 - 72%\nLymphocytes : 14 % 20 - 45%"
    second = "Neutrophils : 81 % 40 - 75%\nLymphocytes : 14 %"   # no range in the second reading: not a disagreement
    monkeypatch.setattr(pdf, "_tesseract", lambda *a, **k: second)
    unsure = pdf._unsure_tests(main, main, Image.new("L", (10, 10)), 0, "x.png", {}, pdf.time.monotonic() + 30)
    assert unsure == {"neutrophils"}
