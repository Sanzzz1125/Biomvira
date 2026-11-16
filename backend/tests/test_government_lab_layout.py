"""A real-world layout: one test group per page, name / (Method: ...) / result on separate lines, a logo image on most pages,
explanatory prose that mentions biomarker names, multi-band lipid reference text and ratio rows."""
import io

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.parsers import pdf_extractor as pdf
from app.parsers.regex_matcher import extract_biomarkers_with_regex, mentioned_keys
from app.parsers.sanitizer import sanitize_report_text

HEAD = ["Patient Name: ASHA RAO Ref. Doctor: Dr. Mehta", "Patient Id: 0001597779 Lab Id: 10262587013", "Age/Gender: 61 Years/Male",
        "CLINICAL BIOCHEMISTRY", "Investigation Result Biological Reference Interval", "Specimen:Serum"]
END = ["*** END OF REPORT ***", "Please correlate clinically", "Test Performed By : Jbhub Consultant Biochemist"]
PAGES = [
    ["HbA1c", "(Method: Immunoturbidimetry)", "6.3 % 4 - 6 %",
     "Interpretation : HbA1c is a form of hemoglobin that is measured primarily to identify the three-month average",
     "plasma glucose concentration"],
    ["LIVER FUNCTION TEST", "S. Bilirubin T", "(Method: DPD)", "0.29 mg/dL 0.3 - 1.2 mg/dL", "S. Bilirubin D", "(Method: DPD)",
     "0.10 mg/dL <0.2 mg/dL", "S.Total Protein", "(Method: Biuret)", "6.4 gm/dL 6.6 - 8.3 gm/dL", "S.Albumin", "(Method: BCG)",
     "4.6 gm/dL 3.5 - 5.2 gm/dL", "Globulin", "(Method: Calculated)", "2 gm/dL 2.6-3.9 gm/dL", "A/G Ratio", "(Method: Calculated)",
     "2.6 1.0 - 1.7", "SGOT/AST", "(Method: UV without P5P)", "14 U/L < 50 U/L", "SGPT /ALT", "(Method: UV without P5P)",
     "22 U/L < 50 U/L", "S.Alkaline Phosphatase", "(Method: IFCC)", "47 U/L 30 - 120 U/L"],
    ["S.Uric Acid", "(Method: Uricase)", "3.5 mg/dL 3.5 - 7.2 mg/dL"],
    ["S. Calcium", "(Method: Arsenazo III)", "7.8 mg/dL 8.8 - 10.6 mg/dL",
     "Interpretation Used in diagnosis & monitoring of a wide range of disorders , including disorders of protein &",
     "vitamin D & diseases of bone, kidney, parathyroid gland or GI tract. Total protein & albumin should",
     "always be measured simultaneously for proper interpretation of serum calcium levels"],
    ["RENAL FUNCTION TEST", "Blood Urea", "(Method: Urease)", "21 mg/dL 17 - 43 mg/dL", "S.Creatinine", "(Method: Enzymatic)",
     "1.35 mg/dL 0.7 - 1.18 mg/dL"],
    ["LIPID PROFILE", "S.Total Cholesterol", "(Method: CHOD-POD)", "136 mg/dL Desirable Level : <200", "mg/dL",
     "Borderline : 200 - 239 mg/dL", "Undesirable : > 240 mg/dL", "S.Triglycerides", "(Method: GPO-POD)",
     "139 mg/dL Desirable Level : <150", "mg/dL", "Borderline : 150 - 199 mg/dL", "High : 200 - 499 mg/dL", "Very High : >500 mg/dL",
     "S.HDL", "(Method: Enzyme Selective Inhibition)", "45 mg/dL Desirable Level : >60 mg/dL", "Borderline : 40 - 59 mg/dL",
     "Undesirable : <40 mg/dL", "VLDL", "(Method: Calculated)", "28 mg/dL <30 mg/dL", "S.LDL", "(Method: Calculated)",
     "63 mg/dL Optimal : <100 mg/dL", "Near Optimal : 100 - 129", "mg/dL", "Borderline High : 130 - 159", "mg/dL",
     "High : 160 - 189 mg/dL", "Very High : >190 mg/dL", "T.Chol/HDL", "(Method: Calculated)", "3.0 Low Risk: 3.3-4.4",
     "Average Risk: 4.5-7.1", "Moderate Risk: 7.2-11.0", "LDL/HDL", "(Method: Calculated)", "1.4 Desirable Level: 0.5-3.0",
     "Borderline Risk: 3.0-6.0", "High Risk: >6.0",
     "Interpretation : The results of this test can identify certain genetic diseases and can determine approximate risks for"],
    ["cardiovascular disease, certain forms of pancreatitis, and other diseases"],  # text-only continuation page
    ["Fasting Blood Glucose", "(Method: Hexokinase)", "135 mg/dL 74-106 mg/dL",
     "Interpretation : Glucose determination is useful in the diagnosis and treatment of Diabetes mellitus. Elevated levels"],
    ["Post Lunch Blood Glucose", "(Method: Hexokinase)", "229 mg/dL <140 mg/dL"],
]
EXPECTED = {
    "hba1c": (6.3, "%"), "bilirubin_total": (0.29, "mg/dL"), "bilirubin_direct": (0.1, "mg/dL"), "globulin": (2, "gm/dL"), "total_protein": (6.4, "gm/dL"), "albumin": (4.6, "gm/dL"),
    "sgot_ast": (14, "U/L"), "sgpt_alt": (22, "U/L"), "alkaline_phosphatase": (47, "U/L"), "uric_acid": (3.5, "mg/dL"),
    "calcium": (7.8, "mg/dL"), "urea": (21, "mg/dL"), "creatinine": (1.35, "mg/dL"), "total_cholesterol": (136, "mg/dL"),
    "triglycerides": (139, "mg/dL"), "hdl_cholesterol": (45, "mg/dL"), "ldl_cholesterol": (63, "mg/dL"),
    "fasting_glucose": (135, "mg/dL"), "postprandial_glucose": (229, "mg/dL"),
}


def make_report():
    logo = Image.new("RGB", (60, 60), "#1a7f64")
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=(595, 842))
    for number, body in enumerate(PAGES):
        text_only = len(body) == 1
        if not text_only and number != 3:
            c.drawImage(ImageReader(logo), 250, 790, width=36, height=36)
        lines = body if text_only else HEAD + body + END
        y = 770
        for line in lines:
            c.drawString(40, y, line)
            y -= 15
        c.drawString(40, 25, "https://example.invalid/ViewFiles.aspx?ReportId=abc   28/10/26, 1:08 PM   Page %d of 9" % (number + 1))
        c.showPage()
    c.save()
    return stream.getvalue()


def test_prose_mentions_are_not_missing_results():
    text = "Interpretation : HbA1c is a form of hemoglobin that is measured primarily\nplasma glucose concentration\n"
    assert "hemoglobin" not in mentioned_keys(text)
    assert mentioned_keys("Hemoglobin (Hb)   10.4   g/dL   12.0 - 15.5") == {"hemoglobin"}
    assert mentioned_keys("S. Calcium\n(Method: Arsenazo III)\n7.8 mg/dL 8.8 - 10.6 mg/dL") == {"calcium"}


def test_whole_real_world_report_is_read_correctly_without_ocr(monkeypatch):
    calls = []
    monkeypatch.setattr(pdf, "ocr_image", lambda image, deadline: calls.append(1) or "")
    text = pdf.extract_upload(make_report(), "report.pdf", "application/pdf")
    assert calls == []  # slow OCR must not run when the text layer is fine
    markers = extract_biomarkers_with_regex(sanitize_report_text(text)[0])
    got = {m.biomarker_key: (m.detected_value, m.detected_unit) for m in markers}
    assert got == EXPECTED
    assert all(not m.warnings for m in markers), [(m.biomarker_key, m.warnings) for m in markers if m.warnings]
    by_key = {m.biomarker_key: m for m in markers}
    # Printed ranges are kept for simple rows; multi-band lipid text gives no (misleading) single range.
    assert (by_key["creatinine"].report_reference_range.low, by_key["creatinine"].report_reference_range.high) == (0.7, 1.18)
    for key in ("total_cholesterol", "triglycerides", "hdl_cholesterol", "ldl_cholesterol"):
        assert by_key[key].report_reference_range is None
    # A one-sided printed range ("<0.2") is kept as an upper limit.
    assert (by_key["bilirubin_direct"].report_reference_range.low, by_key["bilirubin_direct"].report_reference_range.high) == (None, 0.2)
    # VLDL and the ratio rows are not supported tests and must not leak into others.
    assert mentioned_keys(text) - set(got) == set()


def test_ocr_failure_keeps_usable_native_text(monkeypatch):
    def slow(image, deadline):
        raise pdf.ReportError("OCR timed out. Try a clearer or smaller report.")
    monkeypatch.setattr(pdf, "ocr_image", slow)
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=(595, 842))
    c.drawImage(ImageReader(Image.new("RGB", (60, 60), "white")), 250, 780, width=40, height=40)
    c.drawString(50, 740, "Calcium 9.2 mg/dL 8.8 - 10.2")
    c.drawString(50, 722, "Ferritin")
    c.drawString(50, 704, "(value printed only as an image)  15")
    c.showPage(); c.save()
    text = pdf.extract_upload(stream.getvalue(), "scan.pdf", "application/pdf")
    assert "Calcium 9.2" in text  # the report is not rejected just because the optional OCR step failed
