"""Hindi and Telugu versions of the analysis results.

The engine works in English. Before results are shown in another language, every text field is translated:
fixed texts (test names, warnings, foods, tips, advice) from app/data/i18n/{lang}.txt, which hold one translation
per line of strings_en.txt, and the explanation through translated sentence templates so numbers stay exact.
"""
import re
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

LANGUAGES = ("en", "hi", "te")
FOLDER = Path(__file__).resolve().parent / "data" / "i18n"


@lru_cache(maxsize=4)
def table(lang: str) -> dict:
    if lang not in ("hi", "te"):
        return {}
    english = (FOLDER / "strings_en.txt").read_text(encoding="utf-8").split("\n")
    translated = (FOLDER / f"{lang}.txt").read_text(encoding="utf-8").split("\n")
    pairs = {e: t for e, t in zip(english, translated) if e and t}
    # Merged plans use test names without the bracket, e.g. "Hemoglobin · Serum Ferritin".
    short = lambda text: " ".join(re.sub(r"\s*\([^)]*\)", "", text).split())
    for e, t in list(pairs.items()):
        if "(" in e and len(e) < 60 and short(e) not in pairs:
            pairs[short(e)] = short(t)
    return pairs


def tr(text, lang: str):
    if not text or lang == "en" or not isinstance(text, str):
        return text
    return table(lang).get(text, text)


TEMPLATES = {
    "en": {
        "status": {"low": "LOW", "borderline": "BORDERLINE", "high": "HIGH", "normal": "NORMAL"},
        "below": "below the reference range", "above": "above the reference range",
        "above_border": "above the optimal range (borderline)", "below_border": "approaching lower borderline threshold",
        "h_exec": "## Executive Clinical Assessment",
        "all_normal": ("All **{n} tested biomarkers** are within established biological reference intervals. The results "
                       "show balanced values across the tests included in this report. Continue your current varied "
                       "dietary regimen."),
        "summary": ("Analysis of your diagnostic panel reveals that **{a} of {n} parameters** are outside their optimal "
                    "reference intervals ({low} classified as Low, {border} Borderline, {high} Elevated). Where a "
                    "food-based approach is appropriate, the strategy below uses Indian staples matched to your diet and "
                    "allergies. Results that need a doctor's attention are marked clearly, and no food plan replaces "
                    "medical care."),
        "h_impact": "### Physiological Impact Analysis",
        "detail": ("- **{name} ({value} {unit})**: Evaluated as **{status}**, {desc} (Normal Range: {lo} – {hi} "
                   "{unit}; functioning at **{pct}% of optimal**)."),
        "micro_high": ("\n  - *Clinical Relevance:* This value is above the reference ceiling. Nutritional plans avoid "
                       "adding more of this nutrient; please consult a licensed medical practitioner for evaluation."),
        "role": "\n  - *Biological Role:* {x}", "relevance": "\n  - *Clinical Relevance:* {x}",
        "context": "\n  - *Dietary Context:* {x}",
        "h_protocols": "### Targeted Food Protocols", "food_item": "{name} ({amount} per {serving})",
        "protocol": "#### Protocol for {name} ({status})", "priority": "- **Priority Foods:** {foods}.",
        "habit": "- **Helpful Habit:** {x}", "limit": "- **Habit to Limit:** {x}",
        "h_maintain": "### Keeping Healthy Results Healthy",
        "maintain": "- **{name}:** within range. Regular foods that help keep it there: {foods}.",
        "h_attention": "### Clinical Attention Required",
        "alert": ("> [!CAUTION]\n> **Medical Safety Alert:** One or more results need a doctor’s attention; food "
                  "changes alone are not enough. {reasons} Please schedule an appointment with your qualified physician "
                  "for diagnostic review and treatment."),
        "h_roadmap": "### Re-evaluation Roadmap",
        "roadmap": ("Dietary changes usually need **8 to 12 weeks** of consistent adherence before blood values change. "
                    "A follow-up laboratory test after about 10–12 weeks, or sooner if your doctor advises, shows "
                    "whether the changes are working.\n\n*Disclaimer: Biomvira is an educational nutrition-support "
                    "platform grounded in ICMR-NIN reference data. It does not provide medical diagnoses, treatment plans, "
                    "or clinical pharmaceutical prescriptions. Always seek the advice of a qualified physician or certified "
                    "clinical dietitian regarding any health condition.*"),
        "times": ("{name} is more than {factor} times the upper limit of its reference range. Please see a doctor; diet "
                  "changes alone are not enough."),
        "range_below": ("{name} is below its reference range. Biomvira does not give food advice for this test; please "
                        "review it with your doctor."),
        "range_above": ("{name} is above its reference range. Biomvira does not give food advice for this test; please "
                        "review it with your doctor."),
    },
    "hi": {
        "status": {"low": "कम", "borderline": "सीमा पर", "high": "अधिक", "normal": "सामान्य"},
        "below": "संदर्भ सीमा से नीचे", "above": "संदर्भ सीमा से ऊपर",
        "above_border": "उचित सीमा से थोड़ा ऊपर (सीमा पर)", "below_border": "निचली सीमा के क़रीब",
        "h_exec": "## कुल आकलन",
        "all_normal": ("सभी **{n} जाँचें** सामान्य संदर्भ सीमा के भीतर हैं। इस रिपोर्ट की सभी जाँचों में मान संतुलित हैं। "
                       "अपना मौजूदा विविध भोजन जारी रखें।"),
        "summary": ("आपकी जाँच से पता चलता है कि **{n} में से {a} मान** अपनी उचित सीमा से बाहर हैं ({low} कम, {border} सीमा पर, "
                    "{high} अधिक)। जहाँ भोजन से मदद हो सकती है, वहाँ नीचे की योजना आपके आहार और एलर्जी के अनुसार भारतीय भोजन "
                    "सुझाती है। जिन मानों पर डॉक्टर का ध्यान ज़रूरी है, वे साफ़ दिखाए गए हैं; कोई भोजन योजना इलाज की जगह नहीं लेती।"),
        "h_impact": "### शरीर पर असर",
        "detail": ("- **{name} ({value} {unit})**: स्थिति **{status}**, {desc} (सामान्य सीमा: {lo} – {hi} {unit}; "
                   "उचित स्तर का **{pct}%**)।"),
        "micro_high": ("\n  - *महत्व:* यह मान ऊपरी सीमा से अधिक है। भोजन योजना में यह पोषक तत्व और नहीं जोड़ा जाता; कृपया "
                       "जाँच के लिए डॉक्टर से मिलें।"),
        "role": "\n  - *शरीर में काम:* {x}", "relevance": "\n  - *महत्व:* {x}", "context": "\n  - *भोजन से मदद:* {x}",
        "h_protocols": "### भोजन योजना", "food_item": "{name} ({serving} में {amount})",
        "protocol": "#### {name} के लिए ({status})", "priority": "- **मुख्य खाद्य:** {foods}।",
        "habit": "- **अच्छी आदत:** {x}", "limit": "- **कम करें:** {x}",
        "h_maintain": "### सामान्य परिणामों को बनाए रखें",
        "maintain": "- **{name}:** सामान्य सीमा में है। इसे बनाए रखने वाले रोज़ के खाद्य: {foods}।",
        "h_attention": "### डॉक्टर का ध्यान ज़रूरी",
        "alert": ("> [!CAUTION]\n> **स्वास्थ्य चेतावनी:** एक या अधिक परिणामों पर डॉक्टर का ध्यान ज़रूरी है; केवल भोजन बदलना "
                  "काफ़ी नहीं है। {reasons} जाँच और इलाज के लिए कृपया योग्य डॉक्टर से समय लें।"),
        "h_roadmap": "### दोबारा जाँच कब कराएँ",
        "roadmap": ("ख़ून के मान बदलने में आमतौर पर लगातार **8 से 12 हफ़्ते** लगते हैं। लगभग 10–12 हफ़्ते बाद, या डॉक्टर "
                    "की सलाह पर पहले, दोबारा जाँच से पता चलता है कि बदलाव काम कर रहे हैं या नहीं।\n\n*अस्वीकरण: Biomvira "
                    "ICMR-NIN के आँकड़ों पर आधारित एक शैक्षिक पोषण सहायता मंच है। यह बीमारी की पहचान, इलाज या दवा नहीं "
                    "देता। किसी भी स्वास्थ्य समस्या के लिए हमेशा योग्य डॉक्टर या प्रमाणित आहार विशेषज्ञ से सलाह लें।*"),
        "times": ("{name} अपनी संदर्भ सीमा की ऊपरी हद से {factor} गुना से अधिक है। कृपया डॉक्टर से मिलें; केवल भोजन बदलना "
                  "काफ़ी नहीं है।"),
        "range_below": "{name} अपनी संदर्भ सीमा से कम है। Biomvira इस जाँच के लिए भोजन सलाह नहीं देता; कृपया डॉक्टर को दिखाएँ।",
        "range_above": "{name} अपनी संदर्भ सीमा से अधिक है। Biomvira इस जाँच के लिए भोजन सलाह नहीं देता; कृपया डॉक्टर को दिखाएँ।",
    },
    "te": {
        "status": {"low": "తక్కువ", "borderline": "సరిహద్దులో", "high": "ఎక్కువ", "normal": "సాధారణం"},
        "below": "సూచన పరిధి కంటే తక్కువ", "above": "సూచన పరిధి కంటే ఎక్కువ",
        "above_border": "సరైన పరిధి కంటే కొంచెం ఎక్కువ (సరిహద్దులో)", "below_border": "దిగువ సరిహద్దుకు దగ్గరగా",
        "h_exec": "## మొత్తం అంచనా",
        "all_normal": ("మొత్తం **{n} పరీక్షలు** సాధారణ సూచన పరిధిలో ఉన్నాయి. ఈ రిపోర్టులోని అన్ని పరీక్షల విలువలు సమతుల్యంగా "
                       "ఉన్నాయి. మీ ప్రస్తుత వైవిధ్యమైన ఆహారాన్ని కొనసాగించండి."),
        "summary": ("మీ పరీక్షల్లో **{n} లో {a} విలువలు** సరైన పరిధి బయట ఉన్నాయి ({low} తక్కువ, {border} సరిహద్దులో, "
                    "{high} ఎక్కువ). ఆహారంతో సహాయం చేయగలిగిన చోట, కింది ప్రణాళిక మీ ఆహార రకం, అలర్జీలకు తగిన భారతీయ "
                    "ఆహారాలను సూచిస్తుంది. డాక్టర్ దృష్టి అవసరమైన ఫలితాలు స్పష్టంగా గుర్తించబడ్డాయి; ఏ ఆహార ప్రణాళికా వైద్యానికి "
                    "ప్రత్యామ్నాయం కాదు."),
        "h_impact": "### శరీరంపై ప్రభావం",
        "detail": ("- **{name} ({value} {unit})**: స్థితి **{status}**, {desc} (సాధారణ పరిధి: {lo} – {hi} {unit}; "
                   "సరైన స్థాయిలో **{pct}%**)."),
        "micro_high": ("\n  - *ప్రాముఖ్యత:* ఈ విలువ పై పరిమితి కంటే ఎక్కువ. ఆహార ప్రణాళికలో ఈ పోషకాన్ని ఇంకా చేర్చము; దయచేసి "
                       "పరీక్ష కోసం డాక్టర్‌ను సంప్రదించండి."),
        "role": "\n  - *శరీరంలో పాత్ర:* {x}", "relevance": "\n  - *ప్రాముఖ్యత:* {x}", "context": "\n  - *ఆహారంతో సహాయం:* {x}",
        "h_protocols": "### ఆహార ప్రణాళిక", "food_item": "{name} ({serving} లో {amount})",
        "protocol": "#### {name} కోసం ({status})", "priority": "- **ముఖ్య ఆహారాలు:** {foods}.",
        "habit": "- **మంచి అలవాటు:** {x}", "limit": "- **తగ్గించండి:** {x}",
        "h_maintain": "### సాధారణ ఫలితాలను అలాగే ఉంచుకోండి",
        "maintain": "- **{name}:** సాధారణ పరిధిలో ఉంది. దీన్ని అలాగే ఉంచే రోజువారీ ఆహారాలు: {foods}.",
        "h_attention": "### డాక్టర్ దృష్టి అవసరం",
        "alert": ("> [!CAUTION]\n> **ఆరోగ్య హెచ్చరిక:** ఒకటి లేదా అంతకంటే ఎక్కువ ఫలితాలకు డాక్టర్ దృష్టి అవసరం; ఆహార "
                  "మార్పులు మాత్రమే సరిపోవు. {reasons} పరీక్ష, చికిత్స కోసం దయచేసి అర్హత ఉన్న డాక్టర్‌ను కలవండి."),
        "h_roadmap": "### మళ్లీ ఎప్పుడు పరీక్ష చేయించాలి",
        "roadmap": ("రక్త విలువలు మారడానికి సాధారణంగా నిరంతరంగా **8 నుండి 12 వారాలు** పడుతుంది. సుమారు 10–12 వారాల "
                    "తర్వాత, లేదా డాక్టర్ సలహా మేరకు ముందుగానే, మళ్లీ పరీక్ష చేయిస్తే మార్పులు పనిచేస్తున్నాయో తెలుస్తుంది.\n\n"
                    "*గమనిక: Biomvira ICMR-NIN సమాచారం ఆధారంగా పనిచేసే విద్యాపరమైన పోషణ సహాయ వేదిక. ఇది వ్యాధి నిర్ధారణ, "
                    "చికిత్స లేదా మందులు ఇవ్వదు. ఏ ఆరోగ్య సమస్యకైనా ఎప్పుడూ అర్హత ఉన్న డాక్టర్ లేదా ధృవీకృత పోషకాహార నిపుణుల "
                    "సలహా తీసుకోండి.*"),
        "times": ("{name} దాని సూచన పరిధి పై పరిమితి కంటే {factor} రెట్లు ఎక్కువ ఉంది. దయచేసి డాక్టర్‌ను కలవండి; ఆహార "
                  "మార్పులు మాత్రమే సరిపోవు."),
        "range_below": ("{name} దాని సూచన పరిధి కంటే తక్కువ ఉంది. ఈ పరీక్షకు Biomvira ఆహార సలహా ఇవ్వదు; దయచేసి డాక్టర్‌కు "
                        "చూపించండి."),
        "range_above": ("{name} దాని సూచన పరిధి కంటే ఎక్కువ ఉంది. ఈ పరీక్షకు Biomvira ఆహార సలహా ఇవ్వదు; దయచేసి డాక్టర్‌కు "
                        "చూపించండి."),
    },
}


def T(lang: str) -> dict:
    return TEMPLATES.get(lang, TEMPLATES["en"])


_EN = TEMPLATES["en"]
_TIMES = re.compile(r"^(?P<name>.+) is more than (?P<factor>[\d.]+) times the upper limit of its reference range\.")
_RANGE = re.compile(r"^(?P<name>.+) is (?P<where>below|above) its reference range\. Biomvira does not give food advice")


def warning(text, lang: str):
    """A doctor warning in the chosen language: a fixed message, or one of the two templates with the test name."""
    if not text:
        return text
    text = text.replace("NutriLens", "Biomvira")
    if lang == "en":
        return text
    if text in table(lang):
        return table(lang)[text]
    m = _TIMES.match(text)
    if m:
        return T(lang)["times"].format(name=tr(m["name"], lang), factor=m["factor"])
    m = _RANGE.match(text)
    if m:
        return T(lang)[f"range_{m['where']}"].format(name=tr(m["name"], lang))
    return text


def _amount(text: str, lang: str) -> str:
    """'4.2 MG' stays; 'Low GI · High fibre' is translated part by part."""
    return " · ".join(tr(part, lang) for part in text.split(" · "))


def localize_analysis(data: dict, lang: str) -> dict:
    """A copy of a FullAnalysisResponse dict with every text in the chosen language."""
    if lang not in ("hi", "te"):
        return {
            **data,
            "grounded_explanation": data.get("grounded_explanation", "").replace("NutriLens", "Biomvira"),
            "consult_reasons": [warning(x, "en") for x in data.get("consult_reasons", [])],
            "marker_analyses": [
                {**m, "clinical_warning": warning(m.get("clinical_warning"), "en")}
                for m in data.get("marker_analyses", [])
            ],
        }
    from app.engine.explanation_generator import generate_grounded_explanation
    from app.models.schemas import FullAnalysisResponse

    out = deepcopy(data)
    for m in out.get("marker_analyses", []):
        m["display_name"] = tr(m.get("display_name"), lang)
        m["clinical_warning"] = warning(m.get("clinical_warning"), lang)
        m["guideline_threshold"] = tr(m.get("guideline_threshold"), lang)
    for plan in out.get("recommendations", []):
        plan["biomarker_display_name"] = _amount(plan.get("biomarker_display_name") or "", lang)
        plan["absorption_dos"] = [tr(x, lang) for x in plan.get("absorption_dos", [])]
        plan["absorption_donts"] = [tr(x, lang) for x in plan.get("absorption_donts", [])]
        for food in plan.get("recommended_foods", []):
            for key in ("name", "category", "serving_size", "preparation_tip"):
                food[key] = tr(food.get(key), lang)
            food["key_nutrient_yield"] = _amount(food.get("key_nutrient_yield", ""), lang)
            food["synergies"] = [tr(x, lang) for x in food.get("synergies", [])]
    out["consult_reasons"] = [warning(x, lang) for x in out.get("consult_reasons", [])]
    model = FullAnalysisResponse.model_validate(out)
    out["grounded_explanation"], _, _ = generate_grounded_explanation(model.marker_analyses, model.recommendations,
                                                                      lang=lang, user_profile=model.user_profile)
    out["language"] = lang
    return out
