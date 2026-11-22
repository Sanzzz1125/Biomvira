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


AISLE_LABELS = {"grains": "Grains & millets", "pulses": "Pulses & dals", "vegetables": "Vegetables",
                "greens": "Leafy greens", "fruits": "Fruits", "dairy": "Milk & dairy", "meat_fish": "Meat, fish & eggs",
                "nuts_seeds": "Nuts & seeds", "spices": "Spices & masalas", "oils": "Oils & ghee", "other": "Other"}


def generate_diet_plan_pdf(days: list, shopping_list: list, title: str = "Your 7-day diet plan", lang: str = "en") -> bytes:
    lang = lang if lang in ("hi", "te") else "en"
    token = LANG.set(lang)
    try:
        return _build(days, shopping_list, title, lang)
    finally:
        LANG.reset(token)


def _build(days: list, shopping_list: list, title: str, lang: str) -> bytes:
    """The 7-day plan in the report's design: one card per day (four meals side by side), then the shopping list."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import BaseDocTemplate, Frame, KeepTogether, PageTemplate, Paragraph, Spacer

    from app.plan.engine import AISLES, aisle as aisle_of
    from app.plan.nutrition import ingredients
    from app.plan.ingredient_names import INGREDIENTS
    from app.utils import pdf_generator as g

    st = g.ST

    def dish(item: dict) -> str:
        name = ((item.get("names") or {}).get(lang) if lang != "en" else None) or item.get("name", "")
        amount = localize_words(portion(item.get("servings", 1), str(item.get("serving", ""))), lang)
        return f'<b>{g._t(name)}</b><br/><font size="7" color="{g._hex(g.SLATE_500)}">{g._t(amount)}</font>'

    def chip(label: str, value: str):
        return (g.Box([Paragraph(f'<font size="6.6" color="{g._hex(g.SLATE_500)}">{g._t(L(label))}</font><br/>'
                                 f'<font name="{font("Helvetica-Bold")}" size="9" color="{g._hex(g.SLATE_900)}">{value}</font>',
                                 st["small"])], fill=g.SLATE_50, stroke=g.SLATE_200, radius=6, pad_x=7, pad_y=4), None, "left")

    story = [Paragraph(L(title), st["title"]), Spacer(1, 3),
             Paragraph(g._t(L("Built by Biomvira from your report and profile. Amounts are per person. This plan "
                              "supports, and does not replace, advice from your doctor or dietitian.")), st["subtitle"]),
             Spacer(1, 12)]
    for i, day in enumerate(days[:7]):
        totals = day.get("totals") or {}
        meals = day.get("meals") or {}
        columns = []
        for key, label in SLOTS:
            body = "<br/>".join(dish(it) for it in meals.get(key, [])) or "-"
            columns.append((g._stack(Paragraph(g._t(L(label)).upper(), st["eyebrow"]), Spacer(1, 3),
                                     Paragraph(body, st["cell_small"])), None, "left"))
        chips = g.Row([chip("Calories", f"{round(totals.get('energy_kcal', 0))} kcal"),
                       chip("Protein", f"{round(totals.get('protein_g', 0))} g"),
                       chip("Iron", f"{totals.get('iron_mg', 0):.1f} mg"),
                       chip("Calcium", f"{round(totals.get('calcium_mg', 0))} mg"),
                       chip("Salt", f"{day.get('salt_g', 0)} g")], gap=6)
        card = g.Box([Paragraph(g._t(L(DAY_NAMES[i] if len(days) > 1 else "Day plan")), st["card_title"]), Spacer(1, 6),
                      g.Row(columns, gap=10), Spacer(1, 8), chips], accent=g.BRAND_500, pad_y=10)
        story += [KeepTogether([card]), Spacer(1, 10)]

    items = [it for it in shopping_list if it.get("buy_g", 0) >= 5]
    if items:
        table = ingredients()
        groups: dict[str, list] = {}
        for it in items:
            name = it["name"]
            group = it.get("aisle")
            if not group and name in INGREDIENTS:
                codes = INGREDIENTS[name][0]
                group = aisle_of(name, table[codes if isinstance(codes, str) else codes[0]])
            groups.setdefault(group or "other", []).append(it)

        def line(it: dict) -> str:
            name = it["name"]
            if lang != "en":
                name = (it.get("names") or {}).get(lang) or INGREDIENT_NAMES.get(name, (name, name))[lang == "te"]
            grams = it["buy_g"]
            weight = f"{round(grams / 1000, 1)} kg" if grams >= 1000 else f"{-(-grams // 10) * 10} g"
            return f"{g._t(name[:1].upper() + name[1:])} <font color=\"{g._hex(g.SLATE_500)}\">{weight}</font>"

        cards = []
        for key in [a for a in AISLES if a in groups]:
            rows = groups[key]
            half = (len(rows) + 1) // 2
            cols = [(g._stack(*[Paragraph(line(r), st["cell"]) for r in part]), None, "left")
                    for part in (rows[:half], rows[half:]) if part]
            cards.append(g.Box([Paragraph(g._t(L(AISLE_LABELS[key])), st["do_title"]), Spacer(1, 4),
                                g.Row(cols, gap=8)], fill=g.WHITE, pad_y=8))
        story += [g.PageBreak(), g.SectionTitle(L("Shopping list for the week"),
                                                L("Weights as bought, before peeling and cleaning.")), Spacer(1, 8)]
        story += g._grid(cards)

    def header(c, _doc):
        top = g.PAGE_H - 10 * 2.834645669
        g._draw_logo(c, g.MARGIN_X, top - 14, 14)
        c.setFillColor(g.SLATE_900)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(g.MARGIN_X + 19, top - 10, "Biomvira")
        c.setFillColor(g.SLATE_500)
        c.setFont("Helvetica", 7.5)
        c.drawRightString(g.PAGE_W - g.MARGIN_X, top - 10, L("7-day diet plan"))
        c.setStrokeColor(g.SLATE_200)
        c.setLineWidth(0.6)
        c.line(g.MARGIN_X, g.PAGE_H - 16 * 2.834645669, g.PAGE_W - g.MARGIN_X, g.PAGE_H - 16 * 2.834645669)

    buffer = BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4, leftMargin=g.MARGIN_X, rightMargin=g.MARGIN_X, topMargin=g.LATER_TOP,
                          bottomMargin=g.BOTTOM, title=L(title), author="Biomvira")
    frame = Frame(g.MARGIN_X, g.BOTTOM, g.CONTENT_W, g.PAGE_H - g.BOTTOM - g.LATER_TOP, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate("page", [frame], onPage=header)])
    doc.build(story, canvasmaker=g._NumberedCanvas)
    return buffer.getvalue()
