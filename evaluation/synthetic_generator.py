#!/usr/bin/env python3
"""
NutriLens Synthetic Blood Report Generator
Generates realistic Indian diagnostic laboratory blood report PDFs
mimicking Dr. Lal PathLabs, Metropolis, SRL Diagnostics, Apollo, and Thyrocare.
"""
import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

REPORTS = [
    {
        "filename": "report_01_lal_pathlabs_low_vit_d_and_iron.pdf",
        "lab_name": "DR. LAL PATHLABS LTD.",
        "lab_sub": "National Reference Laboratory · NABL & CAP Accredited",
        "accent_color": colors.HexColor("#0D5C75"),
        "patient": {
            "name": "Ananya Sen",
            "age_sex": "26 Y / Female",
            "phone": "+91 98450 12345",
            "ref_by": "Dr. A. K. Banerjee, MD (Med)",
            "uhid": "DEL-9812401",
            "sample_id": "SPL-2026-8812",
            "date": "10-Nov-2026",
        },
        "tests": [
            ("25-OH Vitamin D (Total)", "11.2", "ng/mL", "30.0 - 100.0", "ECLIA"),
            ("Serum Ferritin (Iron Stores)", "8.5", "ng/mL", "15.0 - 307.0", "CLIA"),
            ("Hemoglobin (Hb)", "10.4", "g/dL", "12.0 - 15.5", "Photometry"),
            ("Total Calcium", "9.2", "mg/dL", "8.8 - 10.2", "Arsenazo III"),
        ]
    },
    {
        "filename": "report_02_metropolis_b12_and_folate_deficient.pdf",
        "lab_name": "METROPOLIS HEALTHCARE LTD.",
        "lab_sub": "Center of Diagnostic Excellence · ISO 15189 Certified",
        "accent_color": colors.HexColor("#1A365D"),
        "patient": {
            "name": "Rohan Mehra",
            "age_sex": "29 Y / Male",
            "phone": "+91 97112 34567",
            "ref_by": "Dr. Sunita Deshmukh",
            "uhid": "MUM-4401923",
            "sample_id": "MET-77123",
            "date": "11-Nov-2026",
        },
        "tests": [
            ("Vitamin B12 (Cyanocobalamin)", "132.0", "pg/mL", "211.0 - 911.0", "ECLIA"),
            ("Serum Folate (Vitamin B9)", "3.1", "ng/mL", "4.0 - 20.0", "CLIA"),
            ("25-OH Vitamin D", "18.4", "ng/mL", "30.0 - 100.0", "ECLIA"),
            ("Total Calcium", "8.9", "mg/dL", "8.5 - 10.2", "Spectrophotometry"),
        ]
    },
    {
        "filename": "report_03_srl_severe_anemia_critical_hb.pdf",
        "lab_name": "SRL DIAGNOSTICS",
        "lab_sub": "Clinical Reference Laboratory · Fortis Healthcare Network",
        "accent_color": colors.HexColor("#991B1B"),
        "patient": {
            "name": "Kavita Sharma",
            "age_sex": "23 Y / Female",
            "phone": "+91 99200 88765",
            "ref_by": "Dr. Meenakshi Sundaram",
            "uhid": "BLR-5521098",
            "sample_id": "SRL-99812",
            "date": "12-Nov-2026",
        },
        "tests": [
            ("Hemoglobin (Hb)", "7.4", "g/dL", "12.0 - 15.5", "SLS-Hemoglobin"),
            ("Serum Ferritin", "5.8", "ng/mL", "15.0 - 307.0", "Chemiluminescence"),
            ("25-OH Vitamin D", "8.2", "ng/mL", "30.0 - 100.0", "Chemiluminescence"),
            ("Serum Folate", "2.8", "ng/mL", "4.0 - 20.0", "Chemiluminescence"),
        ]
    },
    {
        "filename": "report_04_apollo_comprehensive_6_markers.pdf",
        "lab_name": "APOLLO DIAGNOSTICS",
        "lab_sub": "Apollo Hospitals Health City · Department of Pathology",
        "accent_color": colors.HexColor("#065F46"),
        "patient": {
            "name": "Vikram Adithya",
            "age_sex": "35 Y / Male",
            "phone": "+91 94440 55667",
            "ref_by": "Dr. R. K. Prasad",
            "uhid": "HYD-1102934",
            "sample_id": "APL-33412",
            "date": "13-Nov-2026",
        },
        "tests": [
            ("25-OH Vitamin D (Total)", "14.8", "ng/mL", "30.0 - 100.0", "ECLIA"),
            ("Vitamin B12 (Cobalamin)", "195.0", "pg/mL", "211.0 - 911.0", "ECLIA"),
            ("Serum Folate (Vit B9)", "4.8", "ng/mL", "4.0 - 20.0", "ECLIA"),
            ("Serum Ferritin", "22.5", "ng/mL", "24.0 - 336.0", "CLIA"),
            ("Hemoglobin (Hb)", "13.2", "g/dL", "13.8 - 17.2", "Impedance"),
            ("Serum Calcium (Total)", "9.1", "mg/dL", "8.8 - 10.2", "Colorimetry"),
        ]
    },
    {
        "filename": "report_05_thyrocare_alternate_si_units.pdf",
        "lab_name": "THYROCARE TECHNOLOGIES LTD.",
        "lab_sub": "The Complete Healthcare People · Central Processing Unit",
        "accent_color": colors.HexColor("#7C2D12"),
        "patient": {
            "name": "Deepak Verma",
            "age_sex": "42 Y / Male",
            "phone": "+91 98110 99887",
            "ref_by": "Self / Wellness Package",
            "uhid": "TC-8891230",
            "sample_id": "TYC-44512",
            "date": "13-Nov-2026",
        },
        "tests": [
            ("25-OH Vitamin D", "32.5", "nmol/L", "75.0 - 250.0", "Photometry"),
            ("Vitamin B12", "140.0", "pmol/L", "155.0 - 672.0", "ECLIA"),
            ("Hemoglobin Total", "125.0", "g/L", "138.0 - 172.0", "Spectrophotometry"),
            ("Total Calcium", "2.15", "mmol/L", "2.20 - 2.55", "Colorimetric"),
        ]
    },
    {
        "filename": "report_06_optimal_healthy_profile.pdf",
        "lab_name": "MAX HEALTHCARE DIAGNOSTICS",
        "lab_sub": "Premier Pathology & Metabolic Lab Network",
        "accent_color": colors.HexColor("#1E3A8A"),
        "patient": {
            "name": "Sneha Kulkarni",
            "age_sex": "28 Y / Female",
            "phone": "+91 98230 44556",
            "ref_by": "Dr. V. N. Joshi",
            "uhid": "MAX-7712093",
            "sample_id": "MAX-11928",
            "date": "13-Nov-2026",
        },
        "tests": [
            ("25-OH Vitamin D", "48.2", "ng/mL", "30.0 - 100.0", "CLIA"),
            ("Vitamin B12", "520.0", "pg/mL", "211.0 - 911.0", "ECLIA"),
            ("Serum Folate", "11.5", "ng/mL", "4.0 - 20.0", "CLIA"),
            ("Serum Ferritin", "68.0", "ng/mL", "15.0 - 307.0", "CLIA"),
            ("Hemoglobin (Hb)", "13.6", "g/dL", "12.0 - 15.5", "SLS"),
            ("Serum Calcium", "9.6", "mg/dL", "8.8 - 10.2", "Arsenazo"),
        ]
    }
]

def generate_pdf(report: dict):
    filepath = os.path.join(OUTPUT_DIR, report["filename"])
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    base = getSampleStyleSheet()
    accent = report["accent_color"]

    story = []

    # 1. Header
    title_style = ParagraphStyle(
        "LabTitle",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=accent,
        alignment=TA_LEFT,
        spaceAfter=2
    )
    sub_style = ParagraphStyle(
        "LabSub",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=8
    )

    story.append(Paragraph(report["lab_name"], title_style))
    story.append(Paragraph(report["lab_sub"], sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=8))

    # 2. Patient Demographics Table
    p = report["patient"]
    demo_data = [
        [f"Patient Name: {p['name']}", f"Age / Sex: {p['age_sex']}", f"Date: {p['date']}"],
        [f"Ref By: {p['ref_by']}", f"Contact: {p['phone']}", f"UHID: {p['uhid']}"],
        [f"Sample ID: {p['sample_id']}", "Sample: Whole Blood / Serum", "Status: Final / Verified"]
    ]
    demo_table = Table(demo_data, colWidths=[6.5*cm, 6.0*cm, 5.5*cm])
    demo_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 14))

    # 3. Section Title
    sec_style = ParagraphStyle(
        "SecHeader",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=accent,
        spaceAfter=6
    )
    story.append(Paragraph("BIOCHEMISTRY & CLINICAL PATHOLOGY", sec_style))

    # 4. Results Table
    th_style = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=9, textColor=colors.white)
    td_name_style = ParagraphStyle("TDName", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.black)
    td_val_style = ParagraphStyle("TDVal", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#0F172A"), alignment=TA_CENTER)
    td_unit_style = ParagraphStyle("TDUnit", fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#334155"), alignment=TA_CENTER)
    td_ref_style = ParagraphStyle("TDRef", fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#475569"), alignment=TA_CENTER)
    td_mth_style = ParagraphStyle("TDMth", fontName="Helvetica-Oblique", fontSize=8, textColor=colors.HexColor("#64748B"), alignment=TA_CENTER)

    test_rows = [[
        Paragraph("Test Description", th_style),
        Paragraph("Observed Value", th_style),
        Paragraph("Unit", th_style),
        Paragraph("Biological Reference Interval", th_style),
        Paragraph("Method", th_style),
    ]]

    for t_name, val, unit, ref, method in report["tests"]:
        test_rows.append([
            Paragraph(t_name, td_name_style),
            Paragraph(val, td_val_style),
            Paragraph(unit, td_unit_style),
            Paragraph(ref, td_ref_style),
            Paragraph(method, td_mth_style),
        ])

    table = Table(test_rows, colWidths=[6.0*cm, 2.8*cm, 2.2*cm, 4.3*cm, 2.7*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))

    # 5. Footer & Sign-offs
    sign_style = ParagraphStyle(
        "Sign",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#475569")
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    sign_data = [
        [
            Paragraph("<b>Dr. Rajesh Gupta, MD</b><br/>Consultant Pathologist", sign_style),
            Paragraph("<b>Dr. P. V. Ramana, PhD</b><br/>Head of Biochemistry", sign_style),
            Paragraph("<b>Electronically Verified</b><br/>No physical signature required", sign_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[6.0*cm, 6.0*cm, 6.0*cm])
    sign_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(sign_table)

    story.append(Spacer(1, 12))
    disclaimer_p = Paragraph(
        "Note: Clinical interpretation should correlate with patient clinical history. "
        "Test results relate only to the sample received.",
        ParagraphStyle("Disc", fontName="Helvetica-Oblique", fontSize=7, textColor=colors.HexColor("#94A3B8"), alignment=TA_CENTER)
    )
    story.append(disclaimer_p)

    doc.build(story)
    print(f"Generated: {filepath} ({os.path.getsize(filepath):,} bytes)")

def main():
    print(f"Generating {len(REPORTS)} realistic synthetic blood report PDFs in '{OUTPUT_DIR}'...\n")
    for r in REPORTS:
        generate_pdf(r)
    print(f"\nAll {len(REPORTS)} reports generated successfully!")

if __name__ == "__main__":
    main()

