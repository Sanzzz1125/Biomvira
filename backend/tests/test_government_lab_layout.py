"""A real-world layout: one test per page, name / (Method: ...) / result on separate lines, a logo image on every
page, explanatory prose that mentions biomarker names, and many tests NutriLens does not support."""
import io

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.parsers import pdf_extractor as pdf
from app.parsers.regex_matcher import extract_biomarkers_with_regex, mentioned_keys
from app.parsers.sanitizer import sanitize_report_text

PAGES = [
    ["Patient Name: ASHA RAO Ref. Doctor: Dr. Mehta", "Age/Gender: 61 Years/Male", "CLINICAL BIOCHEMISTRY",
     "Investigation Result Biological Reference Interval", "HbA1c", "(Method: Immunoturbidimetry)", "6.3 % 4 - 6 %",
     "Interpretation : HbA1c is a form of hemoglobin that is measured primarily to identify the three-month average",
     "plasma glucose concentration", "*** END OF REPORT ***"],
    ["CLINICAL BIOCHEMISTRY", "LIVER FUNCTION TEST", "Investigation Result Biological Reference Interval",
     "S. Bilirubin T", "(Method: DPD)", "0.29 mg/dL 0.3 - 1.2 mg/dL", "S.Total Protein", "(Method: Biuret)", "6.4 gm/dL 6.6 - 8.3 gm/dL",
     "SGOT/AST", "(Method: UV without P5P)", "14 U/L < 50 U/L", "*** END OF REPORT ***"],
    ["CLINICAL BIOCHEMISTRY", "Investigation Result Biological Reference Interval", "S. Calcium", "(Method: Arsenazo III)",
     "7.8 mg/dL 8.8 - 10.6 mg/dL",
     "Interpretation Used in diagnosis & monitoring of a wide range of disorders , including disorders of protein &",
     "vitamin D & diseases of bone, kidney, parathyroid gland or GI tract. Total protein & albumin should",
     "always be measured simultaneously for proper interpretation of serum calcium levels", "*** END OF REPORT ***"],
]


def make_report():
    logo = Image.new("RGB", (60, 60), "#1a7f64")
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=(595, 842))
    for number, lines in enumerate(PAGES):
        if number != 2:  # one page has no logo, like a continuation page
            c.drawImage(ImageReader(logo), 250, 780, width=40, height=40)
        y = 740
        for line in lines:
            c.drawString(50, y, line)
            y -= 18
        c.showPage()
    # a text-only continuation page: no result rows, no image, just the tail of an explanation and a printed footer
    for i, line in enumerate(["cardiovascular disease, certain forms of pancreatitis, and other diseases", "*** END OF REPORT ***",
                              "Please correlate clinically", "Test Performed By : Jbhub Consultant Biochemist"]):
        c.drawString(50, 780 - 18 * i, line)
    c.drawString(50, 40, "https://example.invalid/ViewFiles.aspx?ReportId=abc   28/10/26, 1:08 PM   Page 7 of 9")
    c.showPage()
    c.save()
    return stream.getvalue()


def test_prose_mentions_are_not_missing_results():
    text = "Interpretation : HbA1c is a form of hemoglobin that is measured primarily\nplasma glucose concentration\n"
    assert mentioned_keys(text) == set()
    assert mentioned_keys("Hemoglobin (Hb)   10.4   g/dL   12.0 - 15.5") == {"hemoglobin"}
    assert mentioned_keys("S. Calcium\n(Method: Arsenazo III)\n7.8 mg/dL 8.8 - 10.6 mg/dL") == {"calcium"}


def test_text_pdf_with_logos_never_runs_ocr_and_finds_calcium(monkeypatch):
    calls = []
    monkeypatch.setattr(pdf, "ocr_image", lambda image, deadline: calls.append(1) or "")
    text = pdf.extract_upload(make_report(), "report.pdf", "application/pdf")
    assert calls == []  # slow OCR must not run when the text layer is fine
    markers = extract_biomarkers_with_regex(sanitize_report_text(text)[0])
    assert [(m.biomarker_key, m.detected_value, m.detected_unit) for m in markers] == [("calcium", 7.8, "mg/dL")]
    assert (markers[0].report_reference_range.low, markers[0].report_reference_range.high) == (8.8, 10.6)
    assert mentioned_keys(text) - {m.biomarker_key for m in markers} == set()  # no false "add manually" warnings


def test_ocr_failure_keeps_usable_native_text(monkeypatch):
    def slow(image, deadline):
        raise pdf.ReportError("OCR timed out. Try a clearer or smaller report.")
    monkeypatch.setattr(pdf, "ocr_image", slow)
    # A real row that the text layer lost, on a page with an image, triggers an OCR attempt that then times out.
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=(595, 842))
    c.drawImage(ImageReader(Image.new("RGB", (60, 60), "white")), 250, 780, width=40, height=40)
    for i, line in enumerate(["Calcium 9.2 mg/dL 8.8 - 10.2", "Ferritin"]):
        c.drawString(50, 740 - 18 * i, line)
    c.drawString(50, 700, "(value printed only as an image)  15")
    c.showPage(); c.save()
    text = pdf.extract_upload(stream.getvalue(), "scan.pdf", "application/pdf")
    assert "Calcium 9.2" in text  # the report is not rejected just because the optional OCR step failed
