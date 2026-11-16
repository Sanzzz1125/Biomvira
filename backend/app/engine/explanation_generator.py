from typing import List, Tuple, Dict
from app.engine.rule_engine import BIOMARKERS_CONFIG
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
    "hba1c": {
        "system": "Blood Sugar Control",
        "role": "Reflects average blood glucose over roughly the previous three months, because glucose attaches to haemoglobin inside red blood cells.",
        "depletion_impact": "Higher values mean blood sugar has been running above the healthy range. Values in the diabetes range need confirmation and treatment planning by a doctor.",
        "indian_context": "Diets built on refined cereals and sweets, with little fibre, tend to push blood sugar up.",
        "repletion_strategy": "Build meals around whole grains, millets, pulses and non-starchy vegetables, choose whole fruit over juice, and keep sugar and refined flour small."
    },
    "fasting_glucose": {
        "system": "Blood Sugar Control",
        "role": "Blood glucose after at least eight hours without food, showing how well the body regulates sugar overnight.",
        "depletion_impact": "Values above the healthy range suggest impaired sugar regulation; values in the diabetes range need a doctor's confirmation. Very low values can also need care.",
        "indian_context": "Late heavy dinners and refined carbohydrates can raise fasting glucose over time.",
        "repletion_strategy": "Favour fibre-rich whole grains, millets, pulses and vegetables, and keep sweets and sweetened drinks occasional."
    },
    "postprandial_glucose": {
        "system": "Blood Sugar Control",
        "role": "Blood glucose measured after a meal, showing how strongly a meal raises blood sugar.",
        "depletion_impact": "High post-meal values mean the body is struggling to clear sugar after eating, and values in the diabetes range need a doctor's confirmation.",
        "indian_context": "Large portions of white rice, rotis made of refined flour and sweets raise post-meal glucose sharply.",
        "repletion_strategy": "Pair carbohydrates with dal, sprouts, curd or vegetables, use millets and whole grains, and keep portions steady."
    },
    "total_cholesterol": {
        "system": "Blood Fats and Heart Health",
        "role": "The total amount of cholesterol carried in the blood by all lipoprotein particles.",
        "depletion_impact": "Higher total cholesterol is one of several factors linked with a greater risk of heart and blood-vessel disease, and it must be read together with LDL, HDL and triglycerides.",
        "indian_context": "Deep-fried snacks, bakery items, vanaspati and a lot of ghee add saturated and trans fats to everyday meals.",
        "repletion_strategy": "Eat more fibre from pulses, whole grains and vegetables, use oil in moderation, and replace some saturated fat with nuts and seeds."
    },
    "triglycerides": {
        "system": "Blood Fats and Heart Health",
        "role": "The main form of fat stored and carried in the blood; levels rise after sugary and fatty meals.",
        "depletion_impact": "High triglycerides are linked with heart risk, and very high levels can irritate the pancreas, so they need medical review.",
        "indian_context": "Frequent sweets, refined carbohydrates, fried foods and alcohol are common contributors.",
        "repletion_strategy": "Cut back on sugar and refined flour, choose fibre-rich foods, and include omega-3 sources such as flaxseed or, for non-vegetarians, fish."
    },
    "ldl_cholesterol": {
        "system": "Blood Fats and Heart Health",
        "role": "The cholesterol carried by low-density lipoprotein particles, often called the \u201cbad\u201d cholesterol because it can build up in artery walls.",
        "depletion_impact": "Higher LDL raises the long-term risk of fatty deposits in the arteries; very high values need a doctor's assessment.",
        "indian_context": "Saturated fat from ghee, butter, fried foods and processed meats raises LDL.",
        "repletion_strategy": "Increase soluble fibre from pulses and whole grains, add nuts and seeds, and reduce fried and bakery foods."
    },
    "hdl_cholesterol": {
        "system": "Blood Fats and Heart Health",
        "role": "The cholesterol carried by high-density lipoprotein particles, often called the \u201cgood\u201d cholesterol because it helps clear cholesterol from the blood.",
        "depletion_impact": "Low HDL is linked with a higher heart risk; higher values are protective.",
        "indian_context": "Low physical activity and diets heavy in refined carbohydrates and trans fats are associated with low HDL.",
        "repletion_strategy": "Replace saturated and trans fats with unsaturated fats from nuts, seeds and fish, and stay physically active."
    },
    "creatinine": {
        "system": "Kidney Function",
        "role": "A waste product from muscle that the kidneys filter out of the blood.",
        "depletion_impact": "A value above the range can mean the kidneys are filtering less effectively and needs medical review.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "urea": {
        "system": "Kidney Function",
        "role": "A waste product from protein breakdown that the kidneys remove.",
        "depletion_impact": "A value outside the range can reflect kidney function, hydration or protein intake and should be reviewed by a doctor.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "uric_acid": {
        "system": "Kidney and Joint Health",
        "role": "A waste product from the breakdown of purines in food and body cells.",
        "depletion_impact": "A value outside the range should be reviewed by a doctor; high levels are linked with gout.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "sgot_ast": {
        "system": "Liver Function",
        "role": "An enzyme found in the liver, heart and muscle that rises when these tissues are stressed.",
        "depletion_impact": "A value above the range can point to liver or muscle stress and should be reviewed by a doctor.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "sgpt_alt": {
        "system": "Liver Function",
        "role": "An enzyme found mainly in the liver that rises when liver cells are injured.",
        "depletion_impact": "A value above the range can point to liver stress and should be reviewed by a doctor.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "alkaline_phosphatase": {
        "system": "Liver and Bone",
        "role": "An enzyme found in the liver, bile ducts and bone.",
        "depletion_impact": "A value outside the range should be reviewed by a doctor to find its source.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "bilirubin_total": {
        "system": "Liver Function",
        "role": "A yellow pigment produced when red blood cells break down and cleared by the liver.",
        "depletion_impact": "A value outside the range should be reviewed by a doctor.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "total_protein": {
        "system": "Liver and Nutrition",
        "role": "The total of albumin and globulin proteins in the blood.",
        "depletion_impact": "A value outside the range can reflect liver function, nutrition or inflammation and should be reviewed by a doctor.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "albumin": {
        "system": "Liver and Nutrition",
        "role": "The main protein made by the liver, which keeps fluid in the blood vessels.",
        "depletion_impact": "A value outside the range should be reviewed by a doctor.",
        "indian_context": "",
        "repletion_strategy": "NutriLens does not generate a food plan for this test. Please review it with your doctor."
    },
    "calcium": {
        "system": "Skeletal Density & Neuromuscular Signaling",
        "role": "Mineral electrolyte underpinning bone lattice crystallization, myocardial contractility, and neuromuscular excitation.",
        "depletion_impact": "Persistent dietary shortfalls prompt parathyroid hormone (PTH) release, driving osteoclastic bone resorption to preserve serum calcium, weakening long-term bone mineral density.",
        "indian_context": "Common in non-dairy or lactose-sensitive diets; exacerbated when paired with high-oxalate foods that inhibit bio-absorption.",
        "repletion_strategy": "Consume diverse calcium reservoirs like ragi (finger millet), sesame seeds (til), curd, and green leafy vegetables alongside optimal Vitamin D."
    }
}

_NO_PLAN = "NutriLens does not generate a food plan for this test. Please review it with your doctor."
_CBC, _THY, _ELEC = "Complete Blood Count", "Thyroid Function", "Electrolytes"


def _readonly(system, role, impact):
    return {"system": system, "role": role, "depletion_impact": impact, "indian_context": "", "repletion_strategy": _NO_PLAN}


BIOMARKER_CLINICAL_PROFILES.update({
    "wbc": _readonly(_CBC, "White blood cells fight infection.", "A count outside the range can follow an infection, inflammation or a medicine, and can sometimes point to a blood or immune problem; a doctor should interpret it."),
    "rbc": _readonly(_CBC, "Red blood cells carry oxygen from the lungs to the body.", "A low count is often seen with anaemia; a high count can occur with dehydration or other conditions."),
    "platelets": _readonly(_CBC, "Platelets help blood to clot.", "A low count can raise the risk of bleeding and is common during dengue and some viral fevers; a high count needs review too."),
    "pcv": _readonly(_CBC, "The share of the blood made up of red cells.", "It usually moves with haemoglobin; a low value is often seen with anaemia."),
    "mcv": _readonly(_CBC, "The average size of red blood cells.", "Small cells (low MCV) are typical of iron deficiency; large cells (high MCV) are seen with low vitamin B12 or folate."),
    "mch": _readonly(_CBC, "The average amount of haemoglobin in each red cell.", "A low value often goes with iron deficiency; a high value with large red cells."),
    "mchc": _readonly(_CBC, "How concentrated haemoglobin is inside red cells.", "A low value is often seen with iron deficiency."),
    "rdw": _readonly(_CBC, "How much red cells vary in size.", "A high value is common in early iron, B12 or folate deficiency."),
    "mpv": _readonly(_CBC, "The average size of platelets.", "Interpreted together with the platelet count by a doctor."),
    "esr": _readonly(_CBC, "A general marker of inflammation in the body.", "A raised ESR is non-specific; it can rise with infection, inflammation, anaemia or pregnancy."),
    "tsh": _readonly(_THY, "The pituitary hormone that tells the thyroid gland how much hormone to make.", "A high TSH often means an underactive thyroid and a low TSH an overactive one; thyroid problems are treated by a doctor, not by diet."),
    "t3": _readonly(_THY, "A thyroid hormone that controls the body's energy use.", "Read together with TSH and T4 by a doctor."),
    "t4": _readonly(_THY, "The main hormone made by the thyroid gland.", "Read together with TSH by a doctor."),
    "ft3": _readonly(_THY, "The active, unbound form of T3.", "Read together with TSH and free T4 by a doctor."),
    "ft4": _readonly(_THY, "The unbound form of T4 available to the body.", "Read together with TSH by a doctor."),
    "sodium": _readonly(_ELEC, "Keeps the body's water balance and helps nerves and muscles work.", "Values outside the range can cause weakness or confusion and need medical review."),
    "potassium": _readonly(_ELEC, "Needed for nerve signals and a regular heartbeat.", "Both low and high potassium can affect the heart and need medical review."),
    "chloride": _readonly(_ELEC, "Works with sodium to keep fluid and acid balance.", "Usually interpreted with sodium and other tests."),
    "tibc": _readonly("Iron Studies", "Shows how much iron the blood's carrier protein can hold.", "A high TIBC is common in iron deficiency; the iron plan from your serum iron or ferritin result covers the food side."),
    "ggt": _readonly("Liver Function", "A liver enzyme.", "Raised GGT can be linked to alcohol, fatty liver, medicines or bile-duct problems."),
    "bilirubin_direct": _readonly("Liver Function", "The part of bilirubin already processed by the liver.", "A raised value can point to a liver or bile-flow problem."),
    "bilirubin_indirect": _readonly("Liver Function", "Bilirubin not yet processed by the liver.", "A raised value can come from faster breakdown of red cells or from Gilbert's syndrome."),
    "globulin": _readonly("Liver Function", "Proteins that include the body's antibodies.", "Interpreted together with albumin and total protein."),
    "bun": _readonly("Kidney Function", "The nitrogen part of urea, a waste product cleared by the kidneys.", "Read together with creatinine; dehydration and high protein intake can also raise it."),
    "egfr": _readonly("Kidney Function", "An estimate of how well the kidneys filter the blood, calculated from creatinine, age and sex.", "A value below the range can mean reduced kidney function and needs medical review."),
    "phosphorus": _readonly("Kidney Function", "A mineral that works with calcium for bones and energy.", "Values outside the range are usually linked to kidney, bone or hormone conditions."),
    "crp": _readonly("Inflammation", "A protein the liver makes when there is inflammation.", "A raised CRP usually means infection or inflammation somewhere in the body."),
    "serum_iron": {"system": "Iron Studies", "role": "The amount of iron circulating in the blood, bound to transferrin.", "depletion_impact": "Low serum iron, especially with low ferritin or transferrin saturation, supports iron deficiency.", "indian_context": "", "repletion_strategy": "Iron-rich Indian foods paired with vitamin C, as in the plan below."},
    "transferrin_saturation": {"system": "Iron Studies", "role": "The share of the iron carrier protein that is loaded with iron.", "depletion_impact": "A low saturation means little iron is available for making red blood cells.", "indian_context": "", "repletion_strategy": "Iron-rich Indian foods paired with vitamin C, as in the plan below."},
})
for _cell, _role in (("neutrophils", "the first defence against bacterial infection"), ("lymphocytes", "fight viral infections and make antibodies"),
                     ("eosinophils", "rise with allergies and worm infections"), ("monocytes", "clear damaged cells and germs"),
                     ("basophils", "take part in allergic reactions")):
    _profile = _readonly(_CBC, f"A type of white blood cell; they {_role}." if not _role.startswith("the") else f"A type of white blood cell, {_role}.",
                         "The pattern of white cell types is interpreted by a doctor together with the total count.")
    BIOMARKER_CLINICAL_PROFILES[_cell] = BIOMARKER_CLINICAL_PROFILES[f"{_cell}_abs"] = _profile

def generate_grounded_explanation(
    marker_analyses: List[MarkerAnalysisResult],
    recommendations: List[NutrientRecommendationPlan]
) -> Tuple[str, bool, List[str]]:
    """
    Generates a deterministic, medically safe explanation grounded solely in the structured findings.
    Returns (explanation_text, requires_physician_consult, consult_reasons).
    """
    attention = [m for m in marker_analyses if m.status != MarkerStatus.NORMAL]
    normal = [m for m in marker_analyses if m.status == MarkerStatus.NORMAL]

    consult_reasons = []
    for m in marker_analyses:
        if m.clinical_warning:
            consult_reasons.append(m.clinical_warning)

    requires_physician_consult = len(consult_reasons) > 0

    lines: List[str] = []

    # Section 1: Executive Clinical Assessment
    lines.append("## Executive Clinical Assessment")
    total_markers = len(marker_analyses)

    if not attention:
        lines.append(
            f"All **{total_markers} tested biomarkers** are within established biological reference intervals. "
            "The results show balanced values across the tests included in this report. Continue your current varied dietary regimen."
        )
        return "\n\n".join(lines), requires_physician_consult, consult_reasons

    counts = {s: len([m for m in attention if m.status == s]) for s in (MarkerStatus.LOW, MarkerStatus.BORDERLINE, MarkerStatus.HIGH)}
    lines.append(
        f"Analysis of your diagnostic panel reveals that **{len(attention)} of {total_markers} parameters** "
        f"are outside their optimal reference intervals ({counts[MarkerStatus.LOW]} classified as Low, "
        f"{counts[MarkerStatus.BORDERLINE]} Borderline, {counts[MarkerStatus.HIGH]} Elevated). "
        "Where a food-based approach is appropriate, the strategy below uses Indian staples matched to your diet and allergies. "
        "Results that need a doctor's attention are marked clearly, and no food plan replaces medical care."
    )

    # Section 2: Biomarker findings & physiological impact
    lines.append("### Physiological Impact Analysis")
    for m in attention:
        profile = BIOMARKER_CLINICAL_PROFILES.get(m.biomarker_key, {})
        config = BIOMARKERS_CONFIG.get(m.biomarker_key, {})
        higher_is_worse = config.get("direction", "lower_is_worse") == "higher_is_worse"
        if m.status == MarkerStatus.LOW:
            status_desc = "below the reference range"
        elif m.status == MarkerStatus.HIGH:
            status_desc = "above the reference range"
        elif higher_is_worse:
            status_desc = "above the optimal range (borderline)"
        else:
            status_desc = "approaching lower borderline threshold"

        detail = f"- **{m.display_name} ({m.value} {m.unit})**: Evaluated as **{m.status.value.upper()}**, {status_desc} " \
                 f"(Normal Range: {m.range_low} \u2013 {m.range_high} {m.unit}; functioning at **{m.percentage_of_optimal:.1f}% of optimal**)."
        micronutrient_high = m.status == MarkerStatus.HIGH and not higher_is_worse and config.get("supports_food_plan", True)
        if micronutrient_high:
            detail += ("\n  - *Clinical Relevance:* This value is above the reference ceiling. Nutritional plans avoid adding more of this nutrient; "
                       "please consult a licensed medical practitioner for evaluation.")
        elif profile:
            detail += f"\n  - *Biological Role:* {profile.get('role', '')}"
            detail += f"\n  - *Clinical Relevance:* {profile.get('depletion_impact', '')}"
            detail += f"\n  - *Dietary Context:* {profile.get('repletion_strategy', '')}"
        lines.append(detail)

    # Section 3: Targeted Food Protocol
    improve = [p for p in recommendations if getattr(p, "purpose", "improve") == "improve"]
    maintain = [p for p in recommendations if getattr(p, "purpose", "improve") == "maintain"]
    if improve:
        lines.append("### Targeted Food Protocols")
        for plan in improve:
            top_foods = [f"{f.name} ({f.key_nutrient_yield} per {f.serving_size})" for f in plan.recommended_foods[:3]]
            foods_joined = "; ".join(top_foods)
            lines.append(f"#### Protocol for {plan.biomarker_display_name} ({plan.status.value.upper()})")
            lines.append(f"- **Priority Foods:** {foods_joined}.")

            if plan.absorption_dos:
                lines.append(f"- **Helpful Habit:** {plan.absorption_dos[0]}")
            if plan.absorption_donts:
                lines.append(f"- **Habit to Limit:** {plan.absorption_donts[0]}")

    if maintain:
        lines.append("### Keeping Healthy Results Healthy")
        for plan in maintain:
            foods_joined = ", ".join(f.name for f in plan.recommended_foods)
            lines.append(f"- **{plan.biomarker_display_name}:** within range. Regular foods that help keep it there: {foods_joined}.")

    # Section 5: Clinical Safety Advisory
    if requires_physician_consult:
        lines.append("### Clinical Attention Required")
        lines.append(
            "> [!CAUTION]\n"
            "> **Medical Safety Alert:** One or more results need a doctor\u2019s attention; food changes alone are not enough. "
            + " ".join(consult_reasons)
            + " Please schedule an appointment with your qualified physician for diagnostic review and treatment."
        )

    # Section 6: Recommended Monitoring & Educational Disclaimer
    lines.append("### Re-evaluation Roadmap")
    lines.append(
        "Dietary changes usually need **8 to 12 weeks** of consistent adherence before blood values change. "
        "A follow-up laboratory test after about 10\u201312 weeks, or sooner if your doctor advises, shows whether the changes are working.\n\n"
        "*Disclaimer: NutriLens is an educational nutrition-support platform grounded in ICMR-NIN reference data. "
        "It does not provide medical diagnoses, treatment plans, or clinical pharmaceutical prescriptions. "
        "Always seek the advice of a qualified physician or certified clinical dietitian regarding any health condition.*"
    )

    return "\n\n".join(lines), requires_physician_consult, consult_reasons
