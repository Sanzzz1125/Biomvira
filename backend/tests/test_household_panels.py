"""CBC, ESR, thyroid, electrolytes, iron studies and other common tests, in the layouts Indian labs print them."""
import pytest

from app.engine.recommender import RecommendationEngine
from app.engine.rule_engine import RuleEngine
from app.models.schemas import MarkerInput, MarkerStatus, UserProfile
from app.parsers.regex_matcher import extract_biomarkers_with_regex

REPORT = """[[PAGE 1 native]]
COMPLETE BLOOD COUNT (CBC)
Haemoglobin 10.8 g/dL 12.0 - 15.0 L
Total RBC Count 4.1 mill/cumm 3.8 - 4.8
Packed Cell Volume (PCV) 33.5 % 36 - 46 L
MCV 81.7 fL 83 - 101 L
MCH 26.3 pg 27 - 32 L
MCHC 32.2 g/dL 31.5 - 34.5
RDW-CV 15.8 % 11.6 - 14.0 H
RDW-SD 48.2 fL 39 - 46
Total WBC Count (TLC) 7,850 cells/cumm 4,000 - 11,000
DIFFERENTIAL COUNT
Neutrophils 62 % 40 - 80
Lymphocytes 30 % 20 - 40
Eosinophils 5 % 1 - 6
Monocytes 2.6 % 2 - 10
Basophils 0.4 % 0 - 2
ABSOLUTE COUNTS
Neutrophils 4,867 /cumm 2000 - 7000
Absolute Eosinophil Count 392 /cumm 20 - 500
Platelet Count 1,85,000 /cumm 1,50,000 - 4,10,000
Platelet Distribution Width (PDW) 16.2 fL 9 - 17
Mean Platelet Volume 10.1 fL 7.5 - 11.5
ESR 28 mm/1st hr 0 - 20 H
THYROID PROFILE
T3 Total 1.12 ng/mL 0.8 - 2.0
T4 Total 8.4 µg/dL 5.1 - 14.1
TSH Ultrasensitive 6.82 µIU/mL 0.27 - 4.20 H
Free T4 1.1 ng/dL 0.93 - 1.7
ELECTROLYTES
Serum Sodium 138 mmol/L 136 - 145
Serum Potassium 4.2 mEq/L 3.5 - 5.1
Serum Chloride 101 mmol/L 98 - 107
IRON STUDIES
Serum Iron 38 µg/dL 50 - 170 L
Total Iron Binding Capacity 452 µg/dL 250 - 450 H
UIBC 414 µg/dL 110 - 370
Transferrin Saturation 8.4 % 20 - 50 L
Gamma GT 18 U/L < 38
Blood Urea Nitrogen 11 mg/dL 7 - 20
eGFR 104 mL/min/1.73 m2 > 90
CRP 3.1 mg/L Up to 6.0
"""

EXPECTED = {
    "hemoglobin": (10.8, 10.8), "rbc": (4.1, 4.1), "pcv": (33.5, 33.5), "mcv": (81.7, 81.7), "mch": (26.3, 26.3),
    "mchc": (32.2, 32.2), "rdw": (15.8, 15.8), "wbc": (7850, 7850), "neutrophils": (62, 62), "lymphocytes": (30, 30),
    "eosinophils": (5, 5), "monocytes": (2.6, 2.6), "basophils": (0.4, 0.4), "neutrophils_abs": (4867, 4867),
    "eosinophils_abs": (392, 392), "platelets": (185000, 185), "mpv": (10.1, 10.1), "esr": (28, 28),
    "t3": (1.12, 112), "t4": (8.4, 8.4), "tsh": (6.82, 6.82), "ft4": (1.1, 1.1), "sodium": (138, 138),
    "potassium": (4.2, 4.2), "chloride": (101, 101), "serum_iron": (38, 38), "tibc": (452, 452),
    "transferrin_saturation": (8.4, 8.4), "ggt": (18, 18), "bun": (11, 11), "egfr": (104, 104), "crp": (3.1, 3.1),
}


@pytest.fixture(scope="module")
def markers():
    return {m.biomarker_key: m for m in extract_biomarkers_with_regex(REPORT)}


def test_every_row_is_read_with_the_right_value_and_no_extras(markers):
    assert {k: (m.detected_value, m.canonical_value) for k, m in markers.items()} == EXPECTED
    assert all(not m.warnings for m in markers.values()), {k: m.warnings for k, m in markers.items() if m.warnings}


def test_thousands_separators_and_one_sided_ranges(markers):
    assert (markers["wbc"].report_reference_range.low, markers["wbc"].report_reference_range.high) == (4000, 11000)
    assert markers["platelets"].report_reference_range.low == 150000
    assert (markers["ggt"].report_reference_range.low, markers["ggt"].report_reference_range.high) == (None, 38)
    assert (markers["egfr"].report_reference_range.low, markers["egfr"].report_reference_range.high) == (90, None)
    assert markers["crp"].report_reference_range.high == 6.0


def analyse(markers, profile):
    inputs = [MarkerInput(biomarker_key=k, value=m.detected_value, unit=m.detected_unit,
                          reference_low=m.report_reference_range.low if m.report_reference_range else None,
                          reference_high=m.report_reference_range.high if m.report_reference_range else None)
              for k, m in markers.items()]
    return {r.biomarker_key: r for r in (RuleEngine().evaluate_marker(i, profile) for i in inputs)}


def test_statuses_match_the_lab_flags(markers):
    results = analyse(markers, UserProfile(gender="female", diet_type="veg"))
    flagged = {k: r.status for k, r in results.items() if r.status != MarkerStatus.NORMAL}
    assert flagged == {
        "hemoglobin": MarkerStatus.LOW, "pcv": MarkerStatus.LOW, "mcv": MarkerStatus.LOW, "mch": MarkerStatus.LOW,
        "rdw": MarkerStatus.HIGH, "esr": MarkerStatus.HIGH, "tsh": MarkerStatus.HIGH, "serum_iron": MarkerStatus.LOW,
        "tibc": MarkerStatus.HIGH, "transferrin_saturation": MarkerStatus.LOW,
    }
    # Platelets stay in their own unit (x10^3/µL) with the printed range converted to match.
    assert (results["platelets"].range_low, results["platelets"].range_high) == (150, 410)
    assert (results["egfr"].range_low, results["egfr"].range_high) == (90, 200)
    assert "review it with your doctor" in results["tsh"].clinical_warning


def test_low_iron_studies_lead_to_one_iron_plan_with_varied_indian_foods(markers):
    profile = UserProfile(gender="female", diet_type="veg")
    results = analyse(markers, profile)
    plans = RecommendationEngine().generate_recommendations(list(results.values()), profile)
    iron = [p for p in plans if p.target_biomarker in ("hemoglobin", "serum_iron", "transferrin_saturation")]
    assert iron and all(len(p.recommended_foods) == 8 for p in iron)
    categories = [f.category for f in iron[0].recommended_foods]
    assert max(categories.count(c) for c in categories) <= 2
    # Read-only tests (thyroid, CBC indices) never produce a food plan.
    assert not {p.target_biomarker for p in plans} & {"tsh", "rdw", "esr", "tibc", "pcv"}


def test_danger_levels_are_flagged():
    profile = UserProfile(gender="male")
    potassium = RuleEngine().evaluate_marker(MarkerInput(biomarker_key="potassium", value=6.4, unit="mmol/L"), profile)
    platelets = RuleEngine().evaluate_marker(MarkerInput(biomarker_key="platelets", value=0.4, unit="lakhs/cumm"), profile)
    assert "contact a doctor promptly" in potassium.clinical_warning
    assert platelets.value == 40 and "contact a doctor promptly" in platelets.clinical_warning


def test_real_report_quirks():
    """Layouts seen in real reports: a name in brackets, and a plain count labelled as lakhs."""
    text = ("[[PAGE 1 native]]\nSerum Ferritin (Iron Stores) | 8.5 | ng/mL | 15.0 - 307.0 | CLIA\n"
            "PLATELET COUNT : 2,93,000 Lakhs/cu.mm 1.5 - 4.5 Lakhs/cu.mm\nHAEMOGLOBIN : 12.2 gms % Male : 13.0 - 18.0 gms %\n"
            "MCV 77.9 f l 80 - 99 f l\n")
    got = {m.biomarker_key: m for m in extract_biomarkers_with_regex(text)}
    assert set(got) == {"ferritin", "platelets", "hemoglobin", "mcv"}
    assert got["platelets"].canonical_value == 293
    assert (got["platelets"].report_reference_range.low, got["platelets"].report_reference_range.high) == (150000, 450000)
    assert got["hemoglobin"].canonical_value == 12.2 and got["mcv"].canonical_value == 77.9


def test_value_printed_slightly_above_its_name_stays_on_the_same_row():
    import io
    from reportlab.pdfgen import canvas
    from app.parsers.pdf_extractor import extract_text_and_tables_from_pdf
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=(595, 842))
    for y, name, value in ((700, "MCHC", ": 33.1 g/dL 32 - 36 g/dL"), (677, "NEUTROPHILS", ": 68 % 35 - 70 %"),
                           (654, "LYMPHOCYTES", ": 25 % 20 - 40 %")):
        c.drawString(40, y, name)
        c.drawString(240, y + 4, value)
    c.save()
    got = {m.biomarker_key: m.detected_value for m in extract_biomarkers_with_regex(extract_text_and_tables_from_pdf(stream.getvalue()))}
    assert got == {"mchc": 33.1, "neutrophils": 68, "lymphocytes": 25}


def test_centromed_layout_method_lines_age_and_sex_ranges():
    text = ("[[PAGE 1 native]]\n* SGOT / AST\nMethod:IFCC without pyridoxaal phosphate\n31.5 IU/L Males: Upto 50\nFemales: Upto 35\n"
            "* PROTEIN-TOTAL\nMethod:Biuret\n6.25 g/dL 6.4-8.3\n* M C H C 35.2 g/dL 32.0 - 34.0\n"
            "* CALCIUM\nMethod:NM-BAPTA\n8.97 mg/dL 12–18 years: 8.4 – 10.2\n"
            "* UREA\nMethod:Urease UV\n22.5 mg/dL Female <50yr:15-40\n"
            "A hemoglobin A1c (HbA1c) test measures the amount of blood sugar (glucose) attached to hemoglobin. If HbA1c "
            "levels are high, it may be a sign of diabetes. American Diabetes Association. Standards of medical care in "
            "diabetes—2014. Diabetes Care. 2014 Jan;37 Suppl 1:S14-80.\n")
    got = {m.biomarker_key: m for m in extract_biomarkers_with_regex(text)}
    assert {k: m.detected_value for k, m in got.items()} == {
        "sgot_ast": 31.5, "total_protein": 6.25, "mchc": 35.2, "calcium": 8.97, "urea": 22.5}
    # Age- or sex-specific printed ranges are not guessed; the app's own sex-specific ranges are used.
    assert all(got[k].report_reference_range is None for k in ("sgot_ast", "calcium", "urea"))
    assert not any(m.warnings for m in got.values())


def test_unreadable_picture_page_does_not_fail_a_readable_report(monkeypatch):
    import io
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    import app.parsers.pdf_extractor as pdf
    def timeout(image, deadline, angles=None):
        raise pdf.ReportError("OCR timed out. Try a clearer or smaller report.")
    monkeypatch.setattr(pdf, "ocr_image", timeout)
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=(595, 842))
    c.drawString(40, 700, "Serum Ferritin 14.8 ng/mL 11.0 - 306.8")
    c.showPage()
    c.drawImage(ImageReader(Image.new("RGB", (400, 560), "white")), 0, 0, 595, 842)  # analyser printout page
    c.showPage()
    c.save()
    text = pdf.extract_text_and_tables_from_pdf(stream.getvalue())
    assert "[[PAGE 2 unread]]" in text
    assert [m.detected_value for m in extract_biomarkers_with_regex(text)] == [14.8]
