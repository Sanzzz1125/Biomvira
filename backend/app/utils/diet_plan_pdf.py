"""A4 PDF of a 7-day diet plan with its shopping list (ReportLab), in English, Hindi or Telugu."""
import re
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.plan.ingredient_local import NAMES as INGREDIENT_NAMES
from app.utils.pdf_text import LANG, L, font

BRAND = colors.HexColor("#167c64")
SLOTS = (("breakfast", "Breakfast"), ("lunch", "Lunch"), ("snack", "Evening snack"), ("dinner", "Dinner"))
DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


PLURALS = {"cup": "cups", "roti": "rotis", "katori": "katoris", "glass": "glasses", "phulka": "phulkas",
           "chapati": "chapatis", "plate": "plates", "bowl": "bowls", "paratha": "parathas", "dosa": "dosas",
           "egg": "eggs", "tablespoon": "tablespoons", "piece": "pieces", "ball": "balls", "rotti": "rottis"}

# Serving words in Hindi and Telugu (the same words the website uses).
UNIT_WORDS = {
    "cup": ("कप", "కప్పు"), "cups": ("कप", "కప్పులు"), "cooked": ("पका हुआ", "వండిన"),
    "katori": ("कटोरी", "గిన్నె"), "katoris": ("कटोरी", "గిన్నెలు"), "glass": ("गिलास", "గ్లాసు"),
    "glasses": ("गिलास", "గ్లాసులు"), "plate": ("प्लेट", "ప్లేటు"), "plates": ("प्लेट", "ప్లేట్లు"),
    "bowl": ("कटोरा", "బౌల్"), "bowls": ("कटोरे", "బౌల్స్"), "small": ("छोटी", "చిన్న"), "big": ("बड़ा", "పెద్ద"),
    "medium": ("मध्यम", "మధ్యస్థ"), "piece": ("टुकड़ा", "ముక్క"), "pieces": ("टुकड़े", "ముక్కలు"),
    "tablespoon": ("बड़ा चम्मच", "టేబుల్ స్పూన్"), "tablespoons": ("बड़े चम्मच", "టేబుల్ స్పూన్లు"),
    "handful": ("मुट्ठी", "గుప్పెడు"), "slices": ("स्लाइस", "ముక్కలు"), "roti": ("रोटी", "రొట్టె"),
    "rotis": ("रोटियाँ", "రొట్టెలు"), "idlis": ("इडली", "ఇడ్లీలు"), "dosa": ("डोसा", "దోశ"), "dosas": ("डोसे", "దోశలు"),
    "egg": ("अंडा", "గుడ్డు"), "eggs": ("अंडे", "గుడ్లు"), "phulka": ("फुलका", "పుల్కా"), "phulkas": ("फुलके", "పుల్కాలు"),
    "chapati": ("चपाती", "చపాతీ"), "chapatis": ("चपातियाँ", "చపాతీలు"), "paratha": ("पराठा", "పరాటా"),
    "parathas": ("पराठे", "పరాటాలు"), "puris": ("पूरियाँ", "పూరీలు"), "vadas": ("वड़े", "గారెలు"),
    "ball": ("गोला", "ముద్ద"), "laddu": ("लड्डू", "లడ్డు"), "ladoo": ("लड्डू", "లడ్డు"), "coconut": ("नारियल", "కొబ్బరి"),
    "with": ("के साथ", "తో"), "rotti": ("रोट्टी", "రొట్టె"), "rottis": ("रोट्टियाँ", "రొట్టెలు"),
    "adai": ("अडै", "అడై"),
    "appams": ("अप्पम", "అప్పం"),
    "ariselu": ("अरिसेलु", "అరిసెలు"),
    "baatis": ("बाटियाँ", "బాటీలు"),
    "bajjis": ("बज्जी", "బజ్జీలు"),
    "balls": ("गोले", "ముద్దలు"),
    "bhatura": ("भटूरा", "భటూరా"),
    "bobbattu": ("बोब्बट्टू", "బొబ్బట్టు"),
    "chillas": ("चीले", "చిల్లాలు"),
    "chokha": ("चोखा", "చోఖా"),
    "cob": ("भुट्टा", "కంకి"),
    "dal": ("दाल", "పప్పు"),
    "ghee": ("घी", "నెయ్యి"),
    "gulab": ("गुलाब", "గులాబ్"),
    "jamuns": ("जामुन", "జామూన్లు"),
    "idiyappam": ("इडियप्पम", "ఇడియప్పం"),
    "littis": ("लिट्टी", "లిట్టీలు"),
    "luchis": ("लूची", "లూచీలు"),
    "momos": ("मोमो", "మోమోలు"),
    "neer": ("नीर", "నీర్"),
    "omelette": ("ऑमलेट", "ఆమ్లెట్"),
    "paniyaram": ("पनियारम", "పొంగనాలు"),
    "parotta": ("परोटा", "పరోటా"),
    "pesarattu": ("पेसरट्टू", "పెసరట్టు"),
    "pindi": ("पिंडी", "పిండి"),
    "podi": ("पोडी", "పొడి"),
    "punugulu": ("पुनुगुलु", "పునుగులు"),
    "puttu": ("पुट्टू", "పుట్టు"),
    "rava": ("रवा", "రవ్వ"),
    "rosogollas": ("रसगुल्ले", "రసగుల్లాలు"),
    "samosa": ("समोसा", "సమోసా"),
    "sarva": ("सर्व", "సర్వ"),
    "seeds": ("बीज", "గింజలు"),
    "tbsp": ("बड़ा चम्मच", "టేబుల్ స్పూన్"),
    "thalipeeth": ("थालीपीठ", "థాలిపీఠ్"),
    "thepla": ("थेपला", "తేప్లా"),
    "tikkis": ("टिक्की", "టిక్కీలు"),
    "tsp": ("छोटा चम्मच", "టీ స్పూన్"),
    "uttapam": ("उत्तपम", "ఊతప్పం"),
}


def portion(servings: int, serving: str) -> str:
    """2 and "1 cup cooked" -> "2 cups cooked"."""
    if servings == 1:
        return serving
    words = serving.split(" ", 2)
    if len(words) >= 2 and words[0] == "1" and words[1].lower() in PLURALS:
        return " ".join([str(servings), PLURALS[words[1].lower()], *words[2:]])
    return f"{servings} × {serving}"


def localize_words(text: str, lang: str) -> str:
    """'2 cups cooked' -> '2 कप (पका हुआ)'; words without a translation stay as they are."""
    if lang not in ("hi", "te"):
        return text
    i = 0 if lang == "hi" else 1
    joined = re.fullmatch(r"(.+?) with (.+)", text)  # "2 baatis with dal" -> "dal with 2 baatis" word order
    if joined:
        first, second = (localize_words(part, lang) for part in joined.groups())
        return f"{second} के साथ {first}" if i == 0 else f"{second}తో {first}"
    text = re.sub(r"(\d+) (cups?) cooked",
                  lambda m: f"{m.group(1)} {UNIT_WORDS[m.group(2)][i]} ({'पका हुआ' if i == 0 else 'వండినది'})", text)
    return re.sub(r"[A-Za-z]+", lambda m: UNIT_WORDS.get(m.group(0).lower(), (m.group(0),) * 2)[i], text)


def _esc(text) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_diet_plan_pdf(days: list, shopping_list: list, title: str = "Your 7-day diet plan", lang: str = "en") -> bytes:
    lang = lang if lang in ("hi", "te") else "en"
    token = LANG.set(lang)
    try:
        return _build(days, shopping_list, title, lang)
    finally:
        LANG.reset(token)


def _build(days: list, shopping_list: list, title: str, lang: str) -> bytes:
    regular, bold = font("Helvetica"), font("Helvetica-Bold")
    shaped = {"shaping": 1} if lang != "en" else {}
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=BRAND, fontSize=18, spaceAfter=4, fontName=bold,
                        leading=26 if shaped else 22, **shaped)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceBefore=8, spaceAfter=4, fontName=bold,
                        leading=19 if shaped else 16, **shaped)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=15 if shaped else 13,
                          fontName=regular, **shaped)
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=12 if shaped else 10,
                           textColor=colors.HexColor("#475569"))
    head = ParagraphStyle("head", parent=body, fontName=bold)

    def dish(item: dict) -> str:
        name = (item.get("names") or {}).get(lang) if lang != "en" else None
        amount = localize_words(portion(item.get("servings", 1), item["serving"]), lang)
        return f"{_esc(name or item['name'])} &middot; {_esc(amount)}"

    story = [Paragraph(_esc(L(title)), h1),
             Paragraph(_esc(L("Built by NutriLens from your report and profile. Amounts are per person. This plan "
                              "supports, and does not replace, advice from your doctor or dietitian.")), small),
             Spacer(1, 4 * mm)]
    for i, day in enumerate(days[:7]):
        t = day.get("totals", {})
        story.append(Paragraph(L(DAY_NAMES[i] if len(days) > 1 else "Day plan"), h2))
        rows = [[Paragraph(L("Meal"), head), Paragraph(L("Dishes"), head)]]
        for key, label in SLOTS:
            items = day.get("meals", {}).get(key, [])
            rows.append([Paragraph(L(label), body), Paragraph("<br/>".join(dish(it) for it in items), body)])
        table = Table(rows, colWidths=[36 * mm, 136 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f3ef")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1"))]))
        story.append(table)
        story.append(Paragraph(_esc(L(
            "About {kcal} kcal, protein {protein} g, iron {iron} mg, calcium {calcium} mg, salt about {salt} g.",
            kcal=round(t.get("energy_kcal", 0)), protein=round(t.get("protein_g", 0)), iron=f"{t.get('iron_mg', 0):.1f}",
            calcium=round(t.get("calcium_mg", 0)), salt=day.get("salt_g", 0))), small))
    if shopping_list:
        story += [PageBreak(), Paragraph(L("Shopping list for the week"), h2),
                  Paragraph(L("Weights as bought, before peeling and cleaning."), small), Spacer(1, 2 * mm)]
        items = [i for i in shopping_list if i.get("buy_g", 0) >= 5]

        def label(item: dict) -> str:
            name = item["name"]
            if lang != "en":
                name = (item.get("names") or {}).get(lang) or INGREDIENT_NAMES.get(name, (name, name))[lang == "te"]
            else:
                name = name.capitalize()
            grams = item["buy_g"]
            weight = f"{round(grams / 1000, 1)} kg" if grams >= 1000 else f"{-(-grams // 10) * 10} g"
            return f"{_esc(name)}: {weight}"

        cells = [Paragraph(label(i), body) for i in items]
        rows = [cells[j:j + 3] + [""] * (3 - len(cells[j:j + 3])) for j in range(0, len(cells), 3)]
        table = Table(rows, colWidths=[58 * mm] * 3)
        table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0"))]))
        story.append(table)
    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                      bottomMargin=16 * mm, title=L(title)).build(story)
    return buffer.getvalue()
