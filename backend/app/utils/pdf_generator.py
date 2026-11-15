"""
PDF Export utility for NutriLens nutrition plans.
Generates a branded A4 PDF using ReportLab.
"""
from io import BytesIO
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Brand colours ─────────────────────────────────────────────────────────────
BRAND_BLUE   = colors.HexColor("#2563EB")
BRAND_GREEN  = colors.HexColor("#16A34A")
BRAND_ORANGE = colors.HexColor("#EA580C")
BRAND_RED    = colors.HexColor("#DC2626")
BRAND_GRAY   = colors.HexColor("#6B7280")
LIGHT_BLUE   = colors.HexColor("#EFF6FF")
LIGHT_GREEN  = colors.HexColor("#F0FDF4")
LIGHT_RED    = colors.HexColor("#FEF2F2")

STATUS_COLOUR = {
    "low":        BRAND_RED,
    "borderline": BRAND_ORANGE,
    "normal":     BRAND_GREEN,
    "high":       BRAND_RED,
}
STATUS_BG = {
    "low":        LIGHT_RED,
    "borderline": colors.HexColor("#FFF7ED"),
    "normal":     LIGHT_GREEN,
    "high":       LIGHT_RED,
}


def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "title",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=BRAND_BLUE,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=BRAND_GRAY,
        spaceAfter=10,
        alignment=TA_CENTER,
    )
    styles["section_header"] = ParagraphStyle(
        "section_header",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=BRAND_BLUE,
        spaceBefore=14,
        spaceAfter=4,
        borderPad=0,
    )
    styles["food_name"] = ParagraphStyle(
        "food_name",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.black,
    )
    styles["food_detail"] = ParagraphStyle(
        "food_detail",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=BRAND_GRAY,
        spaceAfter=2,
    )
    styles["synergy"] = ParagraphStyle(
        "synergy",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=BRAND_GREEN,
        spaceAfter=2,
    )
    styles["tip"] = ParagraphStyle(
        "tip",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#374151"),
        spaceAfter=2,
    )
    styles["rule_text"] = ParagraphStyle(
        "rule_text",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.black,
        leftIndent=10,
        spaceAfter=3,
    )
    styles["disclaimer"] = ParagraphStyle(
        "disclaimer",
        parent=base["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=BRAND_GRAY,
        spaceBefore=14,
        alignment=TA_CENTER,
    )
    styles["normal"] = base["Normal"]
    return styles


def _status_badge_table(status: str, value: float, unit: str, range_low: float, range_high: float):
    """Returns a 1-row coloured Table acting as a status badge row."""
    colour = STATUS_COLOUR.get(status, BRAND_GRAY)
    bg     = STATUS_BG.get(status, colors.white)
    label  = status.upper()
    data = [[
        Paragraph(f"<b>{label}</b>", ParagraphStyle("badge", fontName="Helvetica-Bold",
                                                     fontSize=9, textColor=colour)),
        Paragraph(f"<b>{value} {unit}</b>", ParagraphStyle("val", fontName="Helvetica-Bold",
                                                            fontSize=9, textColor=colors.black)),
        Paragraph(f"Ref: {range_low} – {range_high} {unit}",
                  ParagraphStyle("ref", fontName="Helvetica", fontSize=9, textColor=BRAND_GRAY)),
    ]]
    t = Table(data, colWidths=[3.5*cm, 5*cm, 7*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), bg),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [bg]),
        ("BOX",          (0, 0), (-1, -1), 0.5, colour),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def generate_plan_pdf(analysis_data: Dict[str, Any]) -> bytes:
    """
    Build and return a branded A4 PDF as bytes from a FullAnalysisResponse dict.

    Parameters
    ----------
    analysis_data : dict
        The model_dump() of a FullAnalysisResponse object.

    Returns
    -------
    bytes
        Raw PDF bytes ready to stream to the client.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="NutriLens Nutrition Plan",
        author="NutriLens",
    )

    styles = _build_styles()
    story: List = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("🌿 NutriLens", styles["title"]))
    story.append(Paragraph("Personalized Nutrition Plan · From Laboratory Insights", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_BLUE, spaceAfter=10))

    # ── Patient / Session Meta ─────────────────────────────────────────────────
    profile   = analysis_data.get("user_profile", {})
    timestamp = analysis_data.get("timestamp", "")[:10]
    allergens = profile.get("allergens", [])
    allergen_str = ", ".join(allergens).title() if allergens else "None"

    meta_data = [
        ["Report Date", timestamp,         "Diet Type",  profile.get("diet_type", "").title()],
        ["Age / Gender", f"{profile.get('age', '—')} yrs / {profile.get('gender', '').title()}",
         "Allergens", allergen_str],
    ]
    meta_table = Table(meta_data, colWidths=[4*cm, 5.5*cm, 3.5*cm, 4*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",     (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",     (2, 0), (2, -1), "Helvetica-Bold"),
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX",          (0, 0), (-1, -1), 0.5, BRAND_BLUE),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#BFDBFE")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("TEXTCOLOR",    (0, 0), (-1, -1), colors.black),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # ── Status Summary ─────────────────────────────────────────────────────────
    story.append(Paragraph("Biomarker Status Summary", styles["section_header"]))
    summary = analysis_data.get("status_summary", {})
    sum_data = [[
        Paragraph(f"<b>{summary.get('low', 0)}</b><br/><font size=8>Low</font>",
                  ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=16,
                                 textColor=BRAND_RED, alignment=TA_CENTER)),
        Paragraph(f"<b>{summary.get('borderline', 0)}</b><br/><font size=8>Borderline</font>",
                  ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=16,
                                 textColor=BRAND_ORANGE, alignment=TA_CENTER)),
        Paragraph(f"<b>{summary.get('normal', 0)}</b><br/><font size=8>Normal</font>",
                  ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=16,
                                 textColor=BRAND_GREEN, alignment=TA_CENTER)),
        Paragraph(f"<b>{summary.get('high', 0)}</b><br/><font size=8>High</font>",
                  ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=16,
                                 textColor=BRAND_RED, alignment=TA_CENTER)),
    ]]
    sum_table = Table(sum_data, colWidths=[4.25*cm]*4)
    sum_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 10))

    # ── Individual Marker Results ──────────────────────────────────────────────
    story.append(Paragraph("Detailed Marker Analysis", styles["section_header"]))
    for m in analysis_data.get("marker_analyses", []):
        status   = m.get("status", "normal")
        pct      = m.get("percentage_of_optimal", 0)
        badge    = _status_badge_table(
            status, m.get("value", 0), m.get("unit", ""),
            m.get("range_low", 0), m.get("range_high", 0)
        )
        header   = Paragraph(
            f"<b>{m.get('display_name', '')}</b> &nbsp;·&nbsp; {pct}% of lower reference limit",
            ParagraphStyle("mh", fontName="Helvetica-Bold", fontSize=10,
                           textColor=colors.black, spaceAfter=3)
        )
        elements = [header, badge]
        if m.get("clinical_warning"):
            elements.append(
                Paragraph(f"⚠ {m['clinical_warning']}",
                          ParagraphStyle("cw", fontName="Helvetica-Oblique", fontSize=9,
                                         textColor=BRAND_RED, spaceBefore=3))
            )
        elements.append(Spacer(1, 6))
        story.append(KeepTogether(elements))

    # ── Nutrition Recommendation Plans ─────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_BLUE, spaceBefore=6, spaceAfter=10))
    story.append(Paragraph("Personalized Food Recommendations", styles["section_header"]))

    for plan in analysis_data.get("recommendations", []):
        bname  = plan.get("biomarker_display_name", "")
        status = plan.get("status", "")
        story.append(Paragraph(
            f"To support <b>{bname}</b> ({status.title()})",
            ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=11,
                           textColor=BRAND_BLUE, spaceBefore=10, spaceAfter=4)
        ))

        foods = plan.get("recommended_foods", [])
        if foods:
            food_data = [["Food", "Serving", "Key Nutrient", "Tip"]]
            for f in foods:
                tip_text = (f.get("preparation_tip") or "—")[:60]
                food_data.append([
                    Paragraph(f"<b>{f.get('name','')}</b>"
                              + (f"<br/><font size=8 color='#6B7280'>{f.get('hindi_name','')}</font>"
                                 if f.get("hindi_name") else ""),
                              styles["food_name"]),
                    Paragraph(f.get("serving_size", "—"), styles["food_detail"]),
                    Paragraph(f.get("key_nutrient_yield", "—"), styles["food_detail"]),
                    Paragraph(tip_text, styles["food_detail"]),
                ])
            food_table = Table(food_data, colWidths=[5*cm, 3.2*cm, 3*cm, 5.8*cm])
            food_table.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, 0),  BRAND_BLUE),
                ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
                ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",     (0, 0), (-1, 0),  9),
                ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
                ("BOX",          (0, 0), (-1, -1), 0.5, BRAND_BLUE),
                ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#BFDBFE")),
                ("LEFTPADDING",  (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING",   (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
                ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(food_table)
            story.append(Spacer(1, 6))

            # Synergies
            for f in foods:
                for syn in f.get("synergies", []):
                    story.append(Paragraph(f"✦ {f['name']}: {syn}", styles["synergy"]))

        # Absorption dos/don'ts
        dos   = plan.get("absorption_dos", [])
        donts = plan.get("absorption_donts", [])
        if dos:
            story.append(Paragraph("<b>✔ Do:</b>", styles["rule_text"]))
            for d in dos:
                story.append(Paragraph(f"• {d}", styles["rule_text"]))
        if donts:
            story.append(Paragraph("<b>✘ Avoid:</b>", styles["rule_text"]))
            for d in donts:
                story.append(Paragraph(f"• {d}", styles["rule_text"]))

        story.append(Spacer(1, 8))

    # ── Physician Consult Flag ─────────────────────────────────────────────────
    if analysis_data.get("requires_physician_consult"):
        consult_reasons = analysis_data.get("consult_reasons", [])
        reasons_text = "  ".join(consult_reasons)
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND_RED, spaceBefore=8, spaceAfter=6))
        story.append(Paragraph(
            f"⚠ <b>Clinical Attention Advised:</b> {reasons_text}",
            ParagraphStyle("ca", fontName="Helvetica-Bold", fontSize=10,
                           textColor=BRAND_RED, backColor=LIGHT_RED,
                           borderPad=8, spaceBefore=4, spaceAfter=4)
        ))

    # ── Disclaimer ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_GRAY, spaceBefore=16))
    story.append(Paragraph(
        "NutriLens is an educational nutrition-support tool and does NOT provide medical diagnosis, "
        "treatment, or clinical prescription. Always consult a qualified healthcare professional "
        "before altering your dietary or medical regimen.",
        styles["disclaimer"]
    ))

    doc.build(story)
    return buf.getvalue()

