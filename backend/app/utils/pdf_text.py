"""Fixed wording of the downloadable PDFs in Hindi and Telugu.

Texts that come from the analysis itself (test names, foods, tips, warnings) are translated by app.i18n; this file
holds only the PDF's own headings, labels and sentences. Wording matches the website's translations.
"""
from contextvars import ContextVar
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
LANG: ContextVar[str] = ContextVar("pdf_lang", default="en")

# English text -> (Hindi, Telugu). {placeholders} must appear in all three.
TEXT = {
    # status labels and captions
    "Low": ("कम", "తక్కువ"),
    "Borderline": ("सीमा पर", "సరిహద్దులో"),
    "Optimal": ("उचित", "సరైనది"),
    "Elevated": ("अधिक", "ఎక్కువ"),
    # report header and summary
    "Personalized Clinical Nutrition Plan": ("व्यक्तिगत पोषण योजना", "వ్యక్తిగత పోషణ ప్రణాళిక"),
    "Evidence-based nutrition guidance from your lab report": (
        "आपकी लैब रिपोर्ट से प्रमाण-आधारित पोषण मार्गदर्शन", "మీ ల్యాబ్ రిపోర్టు ఆధారంగా పోషణ మార్గదర్శనం"),
    "Ref #{ref}": ("संदर्भ #{ref}", "సూచిక #{ref}"),
    "Page {page} of {total}": ("पृष्ठ {page} / {total}", "పేజీ {page} / {total}"),
    "Biomvira is an educational nutrition tool. It does not replace medical diagnosis or treatment.": (
        "Biomvira एक शैक्षिक पोषण साधन है। यह डॉक्टर की जाँच या इलाज की जगह नहीं लेता।",
        "Biomvira విద్యాపరమైన పోషణ సాధనం. ఇది వైద్య నిర్ధారణకు లేదా చికిత్సకు బదులు కాదు."),
    "Based on {n} laboratory results, for a <b>{diet}</b> diet {exclusions}.": (
        "{n} लैब नतीजों के आधार पर, <b>{diet}</b> आहार के लिए, {exclusions}।",
        "{n} ల్యాబ్ ఫలితాల ఆధారంగా, <b>{diet}</b> ఆహారం కోసం, {exclusions}."),
    "excluding {list}": ("{list} को छोड़कर", "{list} లేకుండా"),
    "with no food exclusions": ("बिना किसी परहेज़ के", "ఏ ఆహారాన్నీ మినహాయించకుండా"),
    "personal": ("व्यक्तिगत", "వ్యక్తిగత"),
    "AGE": ("उम्र", "వయస్సు"),
    "SEX": ("लिंग", "లింగం"),
    "DIET": ("आहार", "ఆహారం"),
    "FOODS EXCLUDED": ("परहेज़", "మినహాయించిన ఆహారాలు"),
    "{n} years": ("{n} वर्ष", "{n} సంవత్సరాలు"),
    "Male": ("पुरुष", "పురుషుడు"),
    "Female": ("महिला", "స్త్రీ"),
    "None": ("कोई नहीं", "ఏదీ లేదు"),
    "Vegetarian": ("शाकाहारी", "శాకాహారం"),
    "Vegan": ("वीगन", "వీగన్"),
    "Eggetarian": ("अंडाहारी", "గుడ్లు తినే శాకాహారం"),
    "Non-vegetarian": ("मांसाहारी", "మాంసాహారం"),
    "Dairy": ("डेयरी", "పాలు"),
    "Gluten": ("ग्लूटेन", "గ్లూటెన్"),
    "Nuts": ("मेवे", "గింజలు"),
    "Soy": ("सोया", "సోయా"),
    "Eggs": ("अंडे", "గుడ్లు"),
    "Seafood": ("समुद्री भोजन", "సముద్ర ఆహారం"),
    "Sesame": ("तिल", "నువ్వులు"),
    "Mustard": ("सरसों", "ఆవాలు"),
    "HEALTH SCORE": ("स्वास्थ्य स्कोर", "ఆరోగ్య స్కోరు"),
    "{a} of {n} results in range": ("{n} में से {a} नतीजे सीमा में", "{n} లో {a} ఫలితాలు పరిధిలో"),
    "All tested laboratory biomarkers are balanced within reference intervals.": (
        "जाँचे गए सभी नतीजे सामान्य सीमा में हैं।", "పరీక్షించిన అన్ని ఫలితాలు సాధారణ పరిధిలో ఉన్నాయి."),
    "{n} need attention; see the plan below.": (
        "{n} नतीजों पर ध्यान देना है; नीचे योजना देखें।", "{n} ఫలితాలకు శ్రద్ధ అవసరం; కింద ప్రణాళిక చూడండి."),
    "{n} needs attention; see the plan below.": (
        "{n} नतीजे पर ध्यान देना है; नीचे योजना देखें।", "{n} ఫలితానికి శ్రద్ధ అవసరం; కింద ప్రణాళిక చూడండి."),
    "OPTIMAL INDEX": ("उचित सूचकांक", "సరైన సూచిక"),
    # doctor warning
    "Please review these results with a doctor": (
        "कृपया इन नतीजों को डॉक्टर को दिखाएँ", "దయచేసి ఈ ఫలితాలను డాక్టర్‌కు చూపించండి"),
    "Food changes can support your health, but the following results need medical advice:": (
        "खान-पान में बदलाव सेहत में मदद करते हैं, पर इन नतीजों के लिए डॉक्टर की सलाह ज़रूरी है:",
        "ఆహార మార్పులు ఆరోగ్యానికి సహాయపడతాయి, కానీ కింది ఫలితాలకు డాక్టర్ సలహా అవసరం:"),
    # tables
    "Results That Need Attention": ("ध्यान देने वाले नतीजे", "శ్రద్ధ అవసరమైన ఫలితాలు"),
    "{n} of your results are outside the healthy range.": (
        "आपके {n} नतीजे स्वस्थ सीमा से बाहर हैं।", "మీ {n} ఫలితాలు ఆరోగ్యకర పరిధికి బయట ఉన్నాయి."),
    "TEST": ("जाँच", "పరీక్ష"),
    "YOUR RESULT": ("आपका नतीजा", "మీ ఫలితం"),
    "RESULT": ("नतीजा", "ఫలితం"),
    "HEALTHY RANGE": ("स्वस्थ सीमा", "ఆరోగ్యకర పరిధి"),
    "STATUS": ("स्थिति", "స్థితి"),
    "WHAT NEXT": ("आगे क्या", "తర్వాత ఏమి"),
    "POSITION IN RANGE": ("सीमा में स्थान", "పరిధిలో స్థానం"),
    "Up to {x}": ("{x} तक", "{x} వరకు"),
    "{x} (Guideline: {y})": ("{x} (दिशानिर्देश: {y})", "{x} (మార్గదర్శకం: {y})"),
    "Doctor review": ("डॉक्टर की जाँच", "డాక్టర్ పరిశీలన"),
    "Food plan": ("भोजन योजना", "ఆహార ప్రణాళిక"),
    "Food plan + doctor": ("भोजन योजना + डॉक्टर", "ఆహార ప్రణాళిక + డాక్టర్"),
    "Monitor": ("नज़र रखें", "గమనిస్తూ ఉండండి"),
    "All Test Results": ("सभी जाँच नतीजे", "అన్ని పరీక్ష ఫలితాలు"),
    "Grouped by panel and compared with the report's reference ranges or clinical guidelines.": (
        "जाँच समूह के अनुसार, रिपोर्ट की सीमा या चिकित्सा दिशानिर्देशों से तुलना करके।",
        "పరీక్షల సమూహం వారీగా, రిపోర్టు పరిధి లేదా వైద్య మార్గదర్శకాలతో పోల్చి."),
    "Other Tests": ("अन्य जाँचें", "ఇతర పరీక్షలు"),
    # food plans
    "Your Food Plan": ("आपकी भोजन योजना", "మీ ఆహార ప్రణాళిక"),
    "Indian foods chosen for each result, matched to your diet and food exclusions. Servings are typical household portions.": (
        "हर नतीजे के लिए चुने गए भारतीय खाद्य, आपके आहार और परहेज़ के अनुसार। मात्रा सामान्य घरेलू माप में है।",
        "ప్రతి ఫలితానికి మీ ఆహారం, మినహాయింపులకు సరిపడే భారతీయ ఆహారాలు. పరిమాణాలు సాధారణ ఇంటి కొలతల్లో ఉన్నాయి."),
    "For {name}": ("{name} के लिए", "{name} కోసం"),
    "FOOD": ("खाद्य", "ఆహారం"),
    "SERVING": ("मात्रा", "పరిమాణం"),
    "PROVIDES": ("देता है", "అందిస్తుంది"),
    "HOW TO EAT IT": ("कैसे खाएँ", "ఎలా తినాలి"),
    "Helpful habits": ("फ़ायदेमंद आदतें", "మంచి అలవాట్లు"),
    "Limit or avoid": ("कम करें या बचें", "తగ్గించండి లేదా మానేయండి"),
    "No foods matched your diet and allergen settings for this result. Please ask a dietitian for suitable alternatives.": (
        "इस नतीजे के लिए आपके आहार और एलर्जी के अनुसार कोई खाद्य नहीं मिला। कृपया डाइटीशियन से विकल्प पूछें।",
        "ఈ ఫలితానికి మీ ఆహారం, అలర్జీలకు సరిపడే ఆహారాలు దొరకలేదు. తగిన ప్రత్యామ్నాయాల కోసం డైటీషియన్‌ను అడగండి."),
    "None of your results needs a corrective food plan. Please review any results marked for a doctor.": (
        "आपके किसी नतीजे के लिए सुधार वाली भोजन योजना की ज़रूरत नहीं है। डॉक्टर के लिए चिह्नित नतीजे ज़रूर दिखाएँ।",
        "మీ ఫలితాలకు సరిదిద్దే ఆహార ప్రణాళిక అవసరం లేదు. డాక్టర్ కోసం గుర్తించిన ఫలితాలను తప్పక చూపించండి."),
    "All your results are within healthy ranges, so no corrective food plan is needed.": (
        "आपके सभी नतीजे स्वस्थ सीमा में हैं, इसलिए सुधार वाली भोजन योजना की ज़रूरत नहीं है।",
        "మీ అన్ని ఫలితాలు ఆరోగ్యకర పరిధిలో ఉన్నాయి, కాబట్టి సరిదిద్దే ఆహార ప్రణాళిక అవసరం లేదు."),
    "Keep Your Healthy Results Healthy": ("अच्छे नतीजों को अच्छा बनाए रखें", "మంచి ఫలితాలను అలాగే నిలుపుకోండి"),
    "These results are within range. Including these foods regularly helps keep them there.": (
        "ये नतीजे सीमा में हैं। इन खाद्यों को नियमित खाने से ये ऐसे ही बने रहते हैं।",
        "ఈ ఫలితాలు పరిధిలో ఉన్నాయి. ఈ ఆహారాలను క్రమం తప్పకుండా తింటే అవి అలాగే ఉంటాయి."),
    "FOODS TO INCLUDE REGULARLY": ("नियमित खाने वाले खाद्य", "క్రమంగా తినవలసిన ఆహారాలు"),
    "TIP": ("सुझाव", "సూచన"),
    "What Your Results Mean": ("आपके नतीजों का मतलब", "మీ ఫలితాల అర్థం"),
    "Plain-language notes for the results outside the healthy range.": (
        "स्वस्थ सीमा से बाहर के नतीजों पर आसान भाषा में जानकारी।",
        "ఆరోగ్యకర పరిధికి బయట ఉన్న ఫలితాలపై సులభమైన వివరణ."),
    "WHAT IT DOES": ("यह क्या करता है", "ఇది ఏమి చేస్తుంది"),
    "WHAT YOUR RESULT MAY MEAN": ("आपके नतीजे का संभावित मतलब", "మీ ఫలితం అర్థం కావచ్చు"),
    "Follow-up": ("आगे की जाँच", "తదుపరి పరీక్ష"),
    "Follow the food plan consistently for 8 to 12 weeks, then repeat the tests that were outside the healthy range, "
    "or earlier if your doctor advises.": (
        "भोजन योजना को 8 से 12 हफ़्ते नियमित अपनाएँ, फिर स्वस्थ सीमा से बाहर वाली जाँचें दोबारा कराएँ, "
        "या डॉक्टर कहें तो पहले।",
        "ఆహార ప్రణాళికను 8 నుండి 12 వారాలు క్రమంగా పాటించి, ఆరోగ్యకర పరిధికి బయట ఉన్న పరీక్షలను మళ్లీ చేయించుకోండి, "
        "డాక్టర్ చెబితే అంతకంటే ముందే."),
    "Retest in 8–12 weeks": ("8–12 हफ़्ते में दोबारा जाँच", "8–12 వారాల్లో మళ్లీ పరీక్ష"),
    "Disclaimer: Biomvira is an educational nutrition-support tool based on ICMR-NIN food composition data and "
    "published clinical reference ranges. It does not diagnose or treat any condition. Please consult a qualified "
    "doctor before changing your diet, medicines or supplements.": (
        "अस्वीकरण: Biomvira, ICMR-NIN के खाद्य आँकड़ों और प्रकाशित चिकित्सा सीमाओं पर आधारित एक शैक्षिक पोषण "
        "साधन है। यह किसी बीमारी की पहचान या इलाज नहीं करता। अपना आहार, दवाएँ या सप्लीमेंट बदलने से पहले योग्य "
        "डॉक्टर से सलाह लें।",
        "గమనిక: Biomvira, ICMR-NIN ఆహార సమాచారం, ప్రచురించిన వైద్య పరిధుల ఆధారంగా పనిచేసే విద్యాపరమైన పోషణ "
        "సాధనం. ఇది ఏ వ్యాధినీ నిర్ధారించదు, చికిత్స చేయదు. మీ ఆహారం, మందులు లేదా సప్లిమెంట్లు మార్చే ముందు "
        "అర్హత ఉన్న డాక్టర్‌ను సంప్రదించండి."),
    # nutrients named under food amounts
    "Iron": ("आयरन", "ఇనుము"),
    "Calcium": ("कैल्शियम", "కాల్షియం"),
    "Folate": ("फ़ोलेट", "ఫోలేట్"),
    "Vitamin D": ("विटामिन D", "విటమిన్ D"),
    "Vitamin B12": ("विटामिन B12", "విటమిన్ B12"),
    # 7-day diet plan
    "Your 7-day diet plan": ("आपकी 7 दिन की आहार योजना", "మీ 7 రోజుల ఆహార ప్రణాళిక"),
    "Built by Biomvira from your report and profile. Amounts are per person. This plan supports, and does not "
    "replace, advice from your doctor or dietitian.": (
        "Biomvira ने आपकी रिपोर्ट और प्रोफ़ाइल से बनाई। मात्रा प्रति व्यक्ति है। यह योजना डॉक्टर या डाइटीशियन की "
        "सलाह में मदद करती है, उसकी जगह नहीं लेती।",
        "మీ రిపోర్టు, ప్రొఫైల్ ఆధారంగా Biomvira తయారు చేసింది. పరిమాణాలు ఒక్కరికి. ఈ ప్రణాళిక డాక్టర్ లేదా "
        "డైటీషియన్ సలహాకు తోడు మాత్రమే, బదులు కాదు."),
    "Familiar": ("जाना-पहचाना", "అలవాటైనది"),
    "Most nutritious": ("सबसे पौष्टिक", "అత్యంత పోషకమైనది"),
    "Regional": ("क्षेत्रीय", "ప్రాంతీయం"),
    "Plan style: {style}. Amounts are per person and each day is built for your calorie, protein and nutrient targets.": (
        "योजना का तरीका: {style}। मात्रा प्रति व्यक्ति है और हर दिन आपकी कैलोरी, प्रोटीन और पोषक लक्ष्यों के लिए बना है।",
        "ప్రణాళిక రకం: {style}. పరిమాణాలు ఒక్కరికి, ప్రతి రోజు మీ కేలరీలు, ప్రోటీన్, పోషక లక్ష్యాలకు తగ్గట్టు తయారైంది."),
    "DAY": ("दिन", "రోజు"),
    "BREAKFAST": ("नाश्ता", "అల్పాహారం"),
    "LUNCH": ("दोपहर का भोजन", "మధ్యాహ్న భోజనం"),
    "EVENING SNACK": ("शाम का नाश्ता", "సాయంత్రం చిరుతిండి"),
    "DINNER": ("रात का भोजन", "రాత్రి భోజనం"),
    "Grains & millets": ("अनाज और मोटे अनाज", "ధాన్యాలు, చిరుధాన్యాలు"),
    "Pulses & dals": ("दालें", "పప్పులు"),
    "Vegetables": ("सब्ज़ियाँ", "కూరగాయలు"),
    "Leafy greens": ("हरी पत्तेदार सब्ज़ियाँ", "ఆకుకూరలు"),
    "Fruits": ("फल", "పండ్లు"),
    "Milk & dairy": ("दूध और डेयरी", "పాలు, పాల ఉత్పత్తులు"),
    "Meat, fish & eggs": ("मांस, मछली और अंडे", "మాంసం, చేపలు, గుడ్లు"),
    "Nuts & seeds": ("मेवे और बीज", "గింజలు, విత్తనాలు"),
    "Spices & masalas": ("मसाले", "మసాలాలు"),
    "Oils & ghee": ("तेल और घी", "నూనెలు, నెయ్యి"),
    "Other": ("अन्य", "ఇతరాలు"),
    "Calories": ("कैलोरी", "కేలరీలు"),
    "Protein": ("प्रोटीन", "ప్రోటీన్"),
    "Salt": ("नमक", "ఉప్పు"),
    "7-day diet plan": ("7 दिन की आहार योजना", "7 రోజుల ఆహార ప్రణాళిక"),
    "Day plan": ("दिन की योजना", "రోజు ప్రణాళిక"),
    "Monday": ("सोमवार", "సోమవారం"),
    "Tuesday": ("मंगलवार", "మంగళవారం"),
    "Wednesday": ("बुधवार", "బుధవారం"),
    "Thursday": ("गुरुवार", "గురువారం"),
    "Friday": ("शुक्रवार", "శుక్రవారం"),
    "Saturday": ("शनिवार", "శనివారం"),
    "Sunday": ("रविवार", "ఆదివారం"),
    "Meal": ("भोजन", "భోజనం"),
    "Dishes": ("व्यंजन", "వంటకాలు"),
    "Breakfast": ("नाश्ता", "అల్పాహారం"),
    "Lunch": ("दोपहर का भोजन", "మధ్యాహ్న భోజనం"),
    "Evening snack": ("शाम का नाश्ता", "సాయంత్రం చిరుతిండి"),
    "Dinner": ("रात का भोजन", "రాత్రి భోజనం"),
    "About {kcal} kcal, protein {protein} g, iron {iron} mg, calcium {calcium} mg, salt about {salt} g.": (
        "लगभग {kcal} kcal, प्रोटीन {protein} g, आयरन {iron} mg, कैल्शियम {calcium} mg, नमक लगभग {salt} g।",
        "సుమారు {kcal} kcal, ప్రోటీన్ {protein} g, ఇనుము {iron} mg, కాల్షియం {calcium} mg, ఉప్పు సుమారు {salt} g."),
    "Shopping list for the week": ("हफ़्ते की ख़रीदारी सूची", "వారానికి కొనుగోలు జాబితా"),
    "Weights as bought, before peeling and cleaning.": (
        "वज़न ख़रीदते समय का है, छीलने और साफ़ करने से पहले।", "బరువులు కొనేటప్పటివి, తొక్క తీసి శుభ్రం చేయక ముందు."),
}

FONTS = {"hi": "NotoSansHi", "te": "NotoSansTe"}


def lang() -> str:
    return LANG.get()


def L(text: str, **values) -> str:
    """The PDF wording in the current language, with {placeholders} filled in."""
    current = LANG.get()
    if current in ("hi", "te") and text in TEXT:
        text = TEXT[text][0 if current == "hi" else 1]
    return text.format(**values) if values else text


def font(name: str) -> str:
    """Helvetica/Courier in English; the Noto font with Latin and the Indian script otherwise."""
    current = LANG.get()
    if current not in FONTS:
        return name
    register_fonts()
    return f"{FONTS[current]}-Bold" if "Bold" in name else f"{FONTS[current]}-Regular"


_registered = False


def register_fonts() -> None:
    global _registered
    if _registered:
        return
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for family in FONTS.values():
        for weight in ("Regular", "Bold"):
            pdfmetrics.registerFont(TTFont(f"{family}-{weight}", str(FONT_DIR / f"{family}-{weight}.ttf")))
        # <b> and <i> inside a paragraph pick the right file (there is no italic: it stays upright).
        # The plain mappings go last so each file maps back to (family, bold, not italic).
        for bold, italic, weight in ((0, 1, "Regular"), (1, 1, "Bold"), (0, 0, "Regular"), (1, 0, "Bold")):
            addMapping(family, bold, italic, f"{family}-{weight}")
    _registered = True
