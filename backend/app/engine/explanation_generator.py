from typing import List, Tuple, Dict
from app.models.schemas import MarkerAnalysisResult, NutrientRecommendationPlan, MarkerStatus

BIOMARKER_CLINICAL_PROFILES: Dict[str, Dict[str, str]] = {
    "vitamin_d": {
        "system": "Musculoskeletal & Immune Regulation",
        "role": "Steroid hormone precursor essential for intestinal calcium absorption, immune barrier function, and bone mineralization.",
        "depletion_impact": "Suboptimal levels impede calcium bioavailability, elevating bone resorption and predisposing to chronic fatigue, musculoskeletal aches, and heightened susceptibility to respiratory infections.",
        "indian_context": "Widespread in urban Indian populations due to modern indoor work patterns, atmospheric UV attenuation, and melanin-mediated reduction in cutaneous synthesis.",
        "repletion_strategy": "Pair dietary fat-soluble sources with healthy lipids (cold-pressed oils, ghee, nuts, whole milk) to optimize micellar intestinal uptake."
    },
    "ferritin": {
        "system": "Hematologic & Cellular Bioenergetics",
        "role": "Primary intracellular storage protein quantifying total-body mobile iron reserves.",
        "depletion_impact": "Depleted ferritin reflects iron store exhaustion before overt microcytic anemia occurs. Causes cellular bioenergetic fatigue, impaired exercise tolerance, brittle nails, and diffuse hair thinning.",
        "indian_context": "Highly prevalent across Indian demographics due to phytate-dense grain staples chelating non-heme iron and widespread habitual post-meal chai consumption.",
        "repletion_strategy": "Combine non-heme iron staples (millets, pulses, greens) with ascorbic acid (lemon, amla) while strictly separating dietary polyphenol tannins (tea/coffee) by at least 60–90 minutes."
    },
    "hemoglobin": {
        "system": "Cardiopulmonary & Oxygen Transport",
        "role": "Erythrocyte metalloprotein executing oxygen delivery from alveoli to peripheral parenchymal tissues.",
        "depletion_impact": "Compromised oxygen-carrying capacity leads to exertional dyspnea, postural lightheadedness, pallor, cold extremities, and reduced physical stamina.",
        "indian_context": "Leading contributor to nutritional anemia in India; closely linked with concurrent iron, folate, and protein deficiencies.",
        "repletion_strategy": "Prioritize iron-dense legumes, leafy greens, and germinated seeds accompanied by adequate bioavailable cofactors."
    },
    "vitamin_b12": {
        "system": "Neurological & One-Carbon Metabolism",
        "role": "Mandatory cofactor for methionine synthase and L-methylmalonyl-CoA mutase, crucial for myelin sheath integrity and RBC maturation.",
        "depletion_impact": "Deficiency induces megaloblastic hematopoiesis, peripheral paresthesias (tingling/numbness in extremities), cognitive slowing ('brain fog'), and elevated homocysteine.",
        "indian_context": "Exceptionally prevalent in strict vegetarian and vegan populations as cobalamin is absent in unfortified plant foods.",
        "repletion_strategy": "Regularly incorporate fermented dairy (curd, paneer) or fortified plant beverages; non-vegetarians benefit from eggs, fish, and lean poultry."
    },
    "folate": {
        "system": "Genomic Synthesis & Cellular Proliferation",
        "role": "Water-soluble B-vitamin coenzyme driving nucleotide synthesis, cellular division, and homocysteine remethylation.",
        "depletion_impact": "Inadequate levels halt rapidly dividing cells, provoking megaloblastic anemia, glossitis, oral ulcerations, and reduced metabolic energy.",
        "indian_context": "Vulnerable to high-heat prolonged Indian cooking methods (prolonged pressure cooking and deep frying) which degrade heat-labile folates.",
        "repletion_strategy": "Incorporate lightly steamed greens, sprouted legumes, chickpeas, and fresh citrus fruits to preserve active folate bioactivity."
    },
    "calcium": {
        "system": "Skeletal Density & Neuromuscular Signaling",
        "role": "Mineral electrolyte underpinning bone lattice crystallization, myocardial contractility, and neuromuscular excitation.",
        "depletion_impact": "Persistent dietary shortfalls prompt parathyroid hormone (PTH) release, driving osteoclastic bone resorption to preserve serum calcium, weakening long-term bone mineral density.",
        "indian_context": "Common in non-dairy or lactose-sensitive diets; exacerbated when paired with high-oxalate foods that inhibit bio-absorption.",
        "repletion_strategy": "Consume diverse calcium reservoirs like ragi (finger millet), sesame seeds (til), curd, and green leafy vegetables alongside optimal Vitamin D."
    }
}

def generate_grounded_explanation(
    marker_analyses: List[MarkerAnalysisResult],
    recommendations: List[NutrientRecommendationPlan]
) -> Tuple[str, bool, List[str]]:
    """
    Generates a deterministic, medically safe explanation grounded solely in the structured findings.
    Returns (explanation_text, requires_physician_consult, consult_reasons).
    """
    flagged = [m for m in marker_analyses if m.status in (MarkerStatus.LOW, MarkerStatus.BORDERLINE)]
    normal = [m for m in marker_analyses if m.status == MarkerStatus.NORMAL]
    high = [m for m in marker_analyses if m.status == MarkerStatus.HIGH]

    consult_reasons = []
    for m in marker_analyses:
        if m.clinical_warning:
            consult_reasons.append(m.clinical_warning)

    requires_physician_consult = len(consult_reasons) > 0

    lines: List[str] = []

    # Section 1: Executive Clinical Assessment
    lines.append("## Executive Clinical Assessment")
    total_markers = len(marker_analyses)
    optimal_count = len(normal)

    if not flagged and not high:
        lines.append(
            f"All **{total_markers} tested biomarkers** are within established biological reference intervals. "
            "Biochemical parameters demonstrate balanced physiological homeostasis across oxygen transport, "
            "bone mineralization, and cellular micronutrient stores. Continue your current varied dietary regimen."
        )
        return "\n\n".join(lines), requires_physician_consult, consult_reasons

    lines.append(
        f"Analysis of your diagnostic panel reveals that **{len(flagged)} of {total_markers} parameters** "
        f"are below optimal biological intervals ({len([m for m in flagged if m.status == MarkerStatus.LOW])} classified as Low, "
        f"{len([m for m in flagged if m.status == MarkerStatus.BORDERLINE])} Borderline). "
        "These micronutrients serve critical roles in vitality, cellular oxygenation, neuro-cognitive health, and skeletal integrity. "
        "The targeted nutritional strategy below is formulated using ICMR-NIN nutrient density data to support biological repletion through whole Indian foods."
    )

    # Section 2: Biomarker Depletion & Physiological Impact
    if flagged:
        lines.append("### Physiological Impact Analysis")
        for m in flagged:
            profile = BIOMARKER_CLINICAL_PROFILES.get(m.biomarker_key, {})
            status_desc = "significantly below reference threshold" if m.status == MarkerStatus.LOW else "approaching lower borderline threshold"
            
            detail = f"- **{m.display_name} ({m.value} {m.unit})**: Evaluated as **{m.status.value.upper()}**, {status_desc} " \
                     f"(Normal Range: {m.range_low} – {m.range_high} {m.unit}; functioning at **{m.percentage_of_optimal:.1f}% of optimal**)."
            
            if profile:
                detail += f"\n  - *Biological Role:* {profile.get('role', '')}"
                detail += f"\n  - *Clinical Relevance:* {profile.get('depletion_impact', '')}"
                detail += f"\n  - *Dietary Context:* {profile.get('repletion_strategy', '')}"
            lines.append(detail)

    # Section 3: Elevated Markers Notice
    if high:
        lines.append("### Elevated Biomarkers")
        for m in high:
            lines.append(
                f"- **{m.display_name}**: Observed value is **{m.value} {m.unit}**, which is elevated above the reference ceiling "
                f"({m.range_low} – {m.range_high} {m.unit}). Nutritional plans are tailored to avoid over-supplementation. "
                "Consult a licensed medical practitioner for clinical evaluation of elevated parameters."
            )

    # Section 4: Targeted Food Protocol & Bioavailability Synergies
    if recommendations:
        lines.append("### Targeted Food Repletion Protocols")
        for plan in recommendations:
            top_foods = [f"{f.name} ({f.key_nutrient_yield} per {f.serving_size})" for f in plan.recommended_foods[:3]]
            foods_joined = "; ".join(top_foods)
            lines.append(f"#### Protocol for {plan.biomarker_display_name} ({plan.status.value.upper()})")
            lines.append(f"- **Priority ICMR-NIN Foods:** {foods_joined}.")
            
            if plan.absorption_dos:
                lines.append(f"- **Synergy Catalyst:** {plan.absorption_dos[0]}")
            if plan.absorption_donts:
                lines.append(f"- **Absorption Inhibitor:** {plan.absorption_donts[0]}")

    # Section 5: Clinical Safety Advisory
    if requires_physician_consult:
        lines.append("### Clinical Attention Required")
        lines.append(
            "> [!CAUTION]\n"
            "> **Medical Safety Alert:** One or more biomarkers have reached critical depletion thresholds where food intervention alone is insufficient. "
            + " ".join(consult_reasons)
            + " Please schedule an appointment with your qualified physician for diagnostic review and medical-grade therapeutic supplementation."
        )

    # Section 6: Recommended Monitoring & Educational Disclaimer
    lines.append("### Re-evaluation Roadmap")
    lines.append(
        "Biological micronutrient repletion typically requires **8 to 12 weeks** of consistent dietary adherence. "
        "A follow-up laboratory blood test is recommended after 10–12 weeks to objectively quantify biomarker restoration.\n\n"
        "*Disclaimer: NutriLens is an educational nutrition-support platform grounded in ICMR-NIN reference data. "
        "It does not provide medical diagnoses, treatment plans, or clinical pharmaceutical prescriptions. "
        "Always seek the advice of a qualified physician or certified clinical dietitian regarding any health condition.*"
    )

    return "\n\n".join(lines), requires_physician_consult, consult_reasons
