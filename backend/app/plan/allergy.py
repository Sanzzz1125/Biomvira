"""Typed allergies ("peanut", "eggplant", "दूध", "పల్లీలు") turned into what to leave out.

A typed word can mean three things, and all that apply are used:
- an allergy group we already label: milk -> dairy, wheat -> gluten, fish -> seafood, til -> sesame. Every dish and
  food carrying that group is left out (a fish allergy leaves out all seafood: the safe reading).
- ingredients: eggplant -> brinjal; groundnut -> peanuts and groundnut oil; chickpea -> chana dal, besan, roasted gram.
  Every dish containing them (also inside a spice mix) and every food card made of them is left out.
- a dish ("sambar", "biryani"): dishes with that name are left out.

Names come from our recipe ingredient names, the official IFCT 2017 names and their regional names in 13 Indian
languages, our Hindi and Telugu market names, dish names, and the hand-written synonyms below. Matching is on whole
words, ignores case and plurals, and forgives one wrong letter in words of five letters or more (two from eight).
A word that matches nothing is reported back as not understood instead of being silently ignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from app.plan.ingredient_local import NAMES as LOCAL_NAMES
from app.plan.ingredient_names import INGREDIENTS, MIXES, TRACE, expand

GROUPS = ("dairy", "gluten", "nuts", "soy", "eggs", "seafood", "sesame", "mustard")

# Words that mean a whole allergy group (English, romanised Hindi/Telugu, Devanagari, Telugu script).
GROUP_WORDS = {
    "dairy": ["dairy", "milk", "milk products", "lactose", "doodh", "dudh", "paal", "paalu", "palu",
              "दूध", "डेयरी", "दुग्ध", "పాలు", "పాల ఉత్పత్తులు", "డెయిరీ"],
    "gluten": ["gluten", "wheat", "gehun", "gehu", "gehoon", "godhuma", "godhumalu", "maida", "atta",
               "गेहूं", "गेहूँ", "ग्लूटेन", "मैदा", "आटा", "గోధుమ", "గోధుమలు", "గ్లూటెన్", "మైదా"],
    "nuts": ["nut", "nuts", "tree nut", "tree nuts", "treenut", "treenuts", "mewa", "meva", "मेवा", "मेवे",
             "గింజలు", "walnut", "hazelnut", "pecan", "macadamia", "brazil nut", "akhrot"],
    "soy": ["soy", "soya", "soybean", "soyabean", "soy bean", "soya bean", "tofu", "सोया", "సోయా"],
    "eggs": ["egg", "eggs", "anda", "ande", "anday", "guddu", "gudlu", "अंडा", "अंडे", "अण्डा", "గుడ్డు", "గుడ్లు"],
    "seafood": ["seafood", "sea food", "fish", "shellfish", "shell fish", "prawn", "shrimp", "crab", "lobster",
                "squid", "oyster", "mussel", "clam", "machli", "machhli", "macchi", "jhinga", "chepa", "chepalu",
                "royyalu", "peetha", "मछली", "झींगा", "समुद्री भोजन", "చేప", "చేపలు", "రొయ్యలు", "పీత"],
    "sesame": ["sesame", "til", "gingelly", "nuvvulu", "nuvvu", "तिल", "నువ్వులు", "నువ్వు"],
    "mustard": ["mustard", "rai", "sarson", "sarso", "avalu", "aavalu", "सरसों", "राई", "ఆవాలు"],
}

# Everyday names for our recipe ingredients that the official and regional names do not cover.
SYNONYMS = {
    "peanuts": ["peanut", "groundnut", "ground nut", "moongphali", "mungfali", "moongfali", "palli", "pallilu",
                "verusenaga", "verushanaga", "shenga", "mungphali", "मूंगफली", "पल्ली", "వేరుశనగ", "పల్లీలు", "పల్లి"],
    "groundnut oil": ["peanut", "groundnut", "ground nut", "moongphali", "mungfali", "palli", "verusenaga",
                      "मूंगफली", "వేరుశనగ", "పల్లీలు"],
    "brinjal": ["eggplant", "aubergine", "baingan", "baigan", "begun", "vankaya", "vangi", "kathirikai", "बैंगन", "వంకాయ"],
    "okra": ["ladies finger", "lady finger", "ladyfinger", "bhindi", "bendakaya", "bendakai", "भिंडी", "బెండకాయ"],
    "capsicum": ["bell pepper", "shimla mirch", "simla mirch", "शिमला मिर्च", "క్యాప్సికం"],
    "kabuli chana": ["chickpea", "garbanzo", "chole", "chhole", "chana", "chanaa", "छोले", "శనగలు"],
    "black chana": ["chickpea", "chana", "kala chana", "shanagalu", "senagalu", "चना", "శనగలు"],
    "chana dal": ["chickpea", "chana", "senaga pappu", "shanaga pappu", "शनगा", "శనగ పప్పు"],
    "besan": ["chickpea", "chana", "gram flour", "chickpea flour", "senaga pindi", "बेसन", "శనగ పిండి"],
    "roasted gram": ["chickpea", "chana", "putnalu", "pappulu", "dalia chana", "భుజియా"],
    "toor dal": ["pigeon pea", "arhar", "tuvar", "toovar", "tur dal", "kandi", "kandi pappu", "अरहर", "కంది పప్పు"],
    "moong dal": ["green gram", "moong", "mung", "mung bean", "pesara", "pesarapappu", "मूंग", "పెసర"],
    "whole moong": ["green gram", "moong", "mung", "mung bean", "pesalu", "pesara", "मूंग", "పెసలు"],
    "urad dal": ["black gram", "urad", "udad", "udid", "minapa", "minapappu", "minumulu", "उड़द", "మినప"],
    "whole urad": ["black gram", "urad", "udad", "minumulu", "उड़द", "మినుములు"],
    "masoor dal": ["lentil", "red lentil", "masoor", "masur", "मसूर"],
    "rajma": ["kidney bean", "kidney beans", "राजमा"],
    "cowpea": ["black eyed pea", "black eyed beans", "lobia", "chawli", "bobbarlu", "alasandalu", "लोबिया", "బొబ్బర్లు"],
    "horse gram": ["kulthi", "ulavalu", "kollu", "कुलथी", "ఉలవలు"],
    "green peas": ["peas", "pea", "matar", "mattar", "batani", "pachi batani", "मटर", "బఠాణీ"],
    "dry peas": ["peas", "pea", "dried peas", "matar", "batani", "मटर", "బఠాణీ"],
    "rice": ["chawal", "chaawal", "biyyam", "annam", "अन्नम", "चावल", "బియ్యం", "అన్నం"],
    "idli rava": ["rice", "idli rice"],
    "rice flakes": ["poha", "aval", "atukulu", "पोहा", "అటుకులు"],
    "puffed rice": ["murmura", "maramaralu", "borugulu", "मुरमुरे", "మరమరాలు"],
    "semolina": ["sooji", "suji", "rava", "rawa", "bombay rava", "upma rava", "सूजी", "రవ్వ"],
    "vermicelli": ["semiya", "sevai", "seviyan", "सेवइयाँ", "సేమియా"],
    "dalia": ["broken wheat", "daliya", "godhuma rava", "दलिया"],
    "maize flour": ["corn", "maize", "makka", "makki", "makai", "mokkajonna", "मक्का", "మొక్కజొన్న"],
    "tender corn": ["corn", "maize", "bhutta", "makka", "makai", "mokkajonna", "भुट्टा", "మొక్కజొన్న"],
    "sweet corn": ["corn", "maize", "makka", "makai", "mokkajonna", "मक्का", "మొక్కజొన్న"],
    "cornflour": ["corn", "maize", "corn starch", "cornstarch"],
    "jowar flour": ["jowar", "sorghum", "jonna", "jonnalu", "ज्वार", "జొన్న"],
    "bajra flour": ["bajra", "pearl millet", "sajja", "sajjalu", "बाजरा", "సజ్జ"],
    "ragi flour": ["ragi", "finger millet", "nachni", "nachani", "मडुआ", "रागी", "రాగి"],
    "little millet": ["samai", "samalu", "kutki", "కుటకి", "సామలు"],
    "potato": ["aloo", "alu", "batata", "bangaladumpa", "aalugadda", "आलू", "బంగాళదుంప", "ఆలూ"],
    "sweet potato": ["shakarkandi", "chilagada", "chilakada dumpa", "शकरकंद", "చిలగడదుంప"],
    "tomato": ["tamatar", "tamata", "tamatar", "टमाटर", "టమాటా", "టమోటా"],
    "onion": ["pyaz", "pyaaz", "kanda", "ullipaya", "ullipayalu", "ulli", "eerulli", "प्याज", "ఉల్లిపాయ", "ఉల్లి"],
    "small onion": ["onion", "shallot", "shallots", "chinna ulli", "ఉల్లి"],
    "spring onion": ["onion", "green onion", "scallion", "hara pyaz", "ఉల్లికాడలు"],
    "garlic": ["lahsun", "lehsun", "vellulli", "veluthulli", "लहसुन", "వెల్లుల్లి"],
    "ginger": ["adrak", "allam", "inji", "अदरक", "అల్లం"],
    "spinach": ["palak", "palakura", "pasalai", "पालक", "పాలకూర"],
    "fenugreek leaves": ["fenugreek", "methi", "menthikura", "मेथी", "మెంతికూర"],
    "fenugreek seeds": ["fenugreek", "methi", "methi dana", "menthulu", "मेथी", "మెంతులు"],
    "amaranth leaves": ["amaranth", "chaulai", "thotakura", "चौलाई", "తోటకూర"],
    "drumstick": ["moringa", "sahjan", "munagakaya", "murungai", "सहजन", "మునగకాయ"],
    "drumstick leaves": ["moringa", "moringa leaves", "sahjan", "munaga aku", "munagaku", "సహజన", "మునగాకు"],
    "gongura": ["roselle", "ambadi", "pitwa", "sorrel leaves", "గోంగూర"],
    "mustard leaves": ["sarson ka saag", "sarson saag"],
    "coriander leaves": ["coriander", "cilantro", "dhaniya", "dhania", "kothimeera", "kothamalli", "धनिया", "కొత్తిమీర"],
    "coriander seeds": ["coriander", "dhaniya", "dhania", "dhaniyalu", "धनिया", "ధనియాలు"],
    "coriander powder": ["coriander", "dhaniya", "dhania", "धनिया"],
    "curry leaves": ["kadi patta", "kadi patta", "karivepaku", "karuveppilai", "करी पत्ता", "కరివేపాకు"],
    "mint leaves": ["mint", "pudina", "पुदीना", "పుదీనా"],
    "green chilli": ["chilli", "chili", "chillies", "mirchi", "mirch", "mirapakaya", "मिर्च", "మిరపకాయ"],
    "dry red chilli": ["chilli", "chili", "chillies", "lal mirch", "endu mirapakaya", "मिर्च", "ఎండు మిరపకాయ"],
    "chilli powder": ["chilli", "chili", "lal mirch", "karam", "mirchi powder", "मिर्च", "కారం"],
    "turmeric": ["haldi", "pasupu", "manjal", "हल्दी", "పసుపు"],
    "cumin seeds": ["cumin", "jeera", "jira", "jeelakarra", "जीरा", "జీలకర్ర"],
    "asafoetida": ["hing", "inguva", "हींग", "ఇంగువ"],
    "black pepper": ["pepper", "kali mirch", "miriyalu", "kalimirch", "काली मिर्च", "మిరియాలు"],
    "cloves": ["clove", "laung", "lavangam", "लौंग", "లవంగాలు"],
    "cardamom": ["elaichi", "ilaichi", "yalakulu", "elakkai", "इलायची", "యాలకులు"],
    "poppy seeds": ["poppy", "khus khus", "khuskhus", "gasagasalu", "खसखस", "గసగసాలు"],
    "ajwain": ["carom", "carom seeds", "vamu", "omam", "अजवाइन", "వాము"],
    "tamarind": ["imli", "chintapandu", "puli", "इमली", "చింతపండు"],
    "jaggery": ["gur", "gud", "bellam", "vellam", "गुड़", "బెల్లం"],
    "sugar": ["cheeni", "chini", "chakkera", "चीनी", "చక్కెర"],
    "honey": ["shahad", "tene", "शहद", "తేనె"],
    "fresh coconut": ["coconut", "nariyal", "kobbari", "thengai", "नारियल", "కొబ్బరి"],
    "dry coconut": ["coconut", "copra", "kopra", "nariyal", "endu kobbari", "नारियल", "కొబ్బరి"],
    "coconut milk": ["coconut", "nariyal", "kobbari", "नारियल", "కొబ్బరి"],
    "coconut water": ["coconut", "nariyal pani", "kobbari neellu", "नारियल", "కొబ్బరి"],
    "coconut oil": ["coconut", "nariyal", "kobbari", "नारियल", "కొబ్బరి"],
    "cashew": ["cashews", "kaju", "jeedipappu", "jeedi pappu", "काजू", "జీడిపప్పు"],
    "almonds": ["almond", "badam", "బాదం", "बादाम"],
    "pistachios": ["pistachio", "pista", "पिस्ता", "పిస్తా"],
    "raisins": ["raisin", "kishmish", "kismis", "draksha", "किशमिश", "కిస్మిస్"],
    "oil": ["sunflower oil", "sunflower", "refined oil"],
    "ghee": ["clarified butter", "desi ghee", "neyyi", "घी", "నెయ్యి"],
    "butter": ["makhan", "venna", "मक्खन", "వెన్న"],
    "curd": ["yogurt", "yoghurt", "dahi", "perugu", "thayir", "दही", "పెరుగు"],
    "buttermilk": ["chaas", "chhaas", "majjiga", "mor", "छाछ", "మజ్జిగ", "curd", "yogurt", "dahi", "perugu"],
    "paneer": ["cottage cheese", "cheese", "पनीर", "పనీర్"],
    "khoa": ["mawa", "khoya", "खोया", "కోవా"],
    "fresh cream": ["cream", "malai", "मलाई", "మీగడ"],
    "soya chunks": ["soy chunks", "meal maker", "nutrela"],
    "chicken": ["meat", "poultry", "murgi", "murga", "kodi", "kodi mamsam", "मुर्गा", "चिकन", "కోడి", "చికెన్"],
    "country chicken": ["meat", "poultry", "chicken", "desi chicken", "natu kodi", "నాటు కోడి"],
    "chicken liver": ["meat", "poultry", "chicken", "liver", "organ meat"],
    "mutton": ["meat", "red meat", "goat", "lamb", "sheep", "gosht", "bakra", "meka", "mamsam", "मटन", "बकरा", "మటన్", "మేక"],
    "mutton liver": ["meat", "red meat", "organ meat", "mutton", "goat", "liver", "kaleji", "कलेजी"],
    "seer fish": ["surmai", "vanjaram", "king fish", "kingfish"],
    "sardine": ["sardines", "mathi", "chaala", "tarli"],
    "mackerel": ["bangda", "ayala", "kanaganthi"],
    "anchovy": ["anchovies", "nethili", "kozhuva"],
    "hilsa": ["ilish", "hilsha"],
    "prawns": ["prawn", "shrimp", "jhinga", "royyalu"],
    "pumpkin": ["kaddu", "gummadi", "kaddoo", "कद्दू", "గుమ్మడి"],
    "ash gourd": ["petha", "budida gummadi", "white pumpkin", "पेठा", "బూడిద గుమ్మడి"],
    "bottle gourd": ["lauki", "ghiya", "dudhi", "sorakaya", "सोरकाया", "लौकी", "సొరకాయ"],
    "bitter gourd": ["karela", "kakarakaya", "pavakkai", "करेला", "కాకరకాయ"],
    "ridge gourd": ["turai", "tori", "beerakaya", "तुरई", "బీరకాయ"],
    "snake gourd": ["chichinda", "potlakaya", "padwal", "చిచిండా", "పొట్లకాయ"],
    "ivy gourd": ["tindora", "kundru", "dondakaya", "kovakkai", "कुंदरू", "దొండకాయ"],
    "cauliflower": ["gobi", "phool gobi", "gobhi", "फूलगोभी", "కాలీఫ్లవర్"],
    "cabbage": ["patta gobi", "band gobhi", "kosu", "క్యాబేజీ", "पत्ता गोभी"],
    "carrot": ["gajar", "गाजर", "క్యారెట్"],
    "beetroot": ["beet", "chukandar", "चुकंदर", "బీట్‌రూట్"],
    "radish": ["mooli", "mullangi", "मूली", "ముల్లంగి"],
    "cucumber": ["kheera", "khira", "dosakaya", "खीरा", "దోసకాయ"],
    "yellow cucumber": ["cucumber", "dosakaya", "దోసకాయ"],
    "french beans": ["beans", "green beans", "frans beans"],
    "cluster beans": ["gawar", "guar", "goruchikkudu", "ग्वार", "గోరుచిక్కుడు"],
    "field beans": ["sem", "papdi", "chikkudu", "chikkudukaya", "సెం", "చిక్కుడు"],
    "colocasia": ["arbi", "taro", "chamagadda", "seppankizhangu", "अरबी", "చామగడ్డ"],
    "elephant yam": ["yam", "suran", "jimikand", "kanda gadda", "సురన్", "కంద"],
    "tapioca": ["cassava", "kappa", "karrapendalam", "కర్రపెండలం"],
    "sago": ["sabudana", "saggubiyyam", "javvarisi", "साबूदाना", "సగ్గుబియ్యం"],
    "raw banana": ["banana", "plantain", "kachcha kela", "aratikaya", "అరటికాయ"],
    "ripe plantain": ["banana", "plantain", "nendran"],
    "banana": ["kela", "arati pandu", "aratipandu", "केला", "అరటిపండు"],
    "raw mango": ["mango", "kairi", "kacha aam", "mamidikaya", "మామిడికాయ"],
    "mango": ["aam", "mamidi", "mamidipandu", "आम", "మామిడి"],
    "guava": ["amrud", "jama", "jamakaya", "अमरूद", "జామ"],
    "papaya": ["papita", "boppayi", "बोप्पायि", "पपीता", "బొప్పాయి"],
    "pomegranate": ["anar", "danimma", "anaar", "अनार", "దానిమ్మ"],
    "watermelon": ["tarbooz", "tarbuj", "puchakaya", "तरबूज", "పుచ్చకాయ"],
    "sapota": ["chikoo", "chiku", "sapota", "సపోటా", "चीकू"],
    "grapes": ["grape", "angoor", "draksha", "अंगूर", "ద్రాక్ష"],
    "apple": ["seb", "सेब", "ఆపిల్"],
    "orange": ["santra", "narinja", "kamala", "संतरा", "నారింజ"],
    "mushroom": ["khumb", "kukurmutta", "puttagodugu", "మష్రూమ్", "मशरूम"],
    "tinda": ["round gourd", "indian squash", "टिंडा"],
    "parwal": ["pointed gourd", "parval", "परवल"],
    "chow chow": ["chayote", "seemebadanekai"],
    "knol khol": ["kohlrabi", "ganth gobhi", "noolkol"],
    "bathua": ["chenopodium", "pappu kura", "बथुआ"],
    "ponnaganti": ["ponnaganni", "sessile joyweed", "ponnaganti kura"],
    "lemon juice": ["lemon", "lime", "nimbu", "nimmakaya", "नींबू", "నిమ్మకాయ"],
    "salt": ["namak", "uppu", "नमक", "ఉప్పు"],
    "black salt": ["kala namak", "salt", "काला नमक"],
    "oats": ["oat", "jai"],
    "whole wheat bread": ["bread", "brown bread"],
}

# Foods people are allergic to that none of our dishes or food cards contain. Recognised, so the person is told
# "no dish contains it" instead of "not understood".
NOT_USED = ["kiwi", "strawberry", "celery", "lupin", "chocolate", "cocoa", "pineapple", "avocado", "quinoa",
            "buckwheat", "rye", "corn syrup", "gelatin", "mustard sauce", "msg", "alcohol"]

GENERIC = {"raw", "fresh", "dry", "dried", "whole", "green", "red", "white", "black", "brown", "yellow", "boiled",
           "cooked", "roasted", "fried", "powder", "paste", "flour", "oil", "leaves", "leaf", "seed", "seeds", "sauce",
           "mix", "masala", "all", "varieties", "variety", "ripe", "tender", "big", "small", "country", "juice",
           "water", "milk", "liver", "beans", "bean", "pea", "gram", "fish", "pulse", "pulses", "vegetable", "vegetables",
           "fruit", "fruits", "meat", "spice", "spices", "food", "foods", "and", "with", "of", "the", "in"}


def _singular(word: str) -> str:
    if not word.isascii() or len(word) <= 3:
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def norm(text: str) -> tuple:
    """Words of a name, lower case and singular; punctuation and the IFCT ', raw' style separators dropped."""
    words = re.findall(r"[\wऀ-ॿఀ-౿]+", (text or "").lower())
    return tuple(_singular(w) for w in words if w)


def _contains(alias: tuple, phrase: tuple) -> bool:
    """phrase appears in alias as consecutive whole words."""
    n = len(phrase)
    return any(alias[i:i + n] == phrase for i in range(len(alias) - n + 1))


def _close(a: str, b: str) -> bool:
    """One edit apart (two for long words), counting a swap of neighbours as one edit."""
    if not (a.isascii() and b.isascii()):
        return False
    limit = 2 if min(len(a), len(b)) >= 8 else 1
    if abs(len(a) - len(b)) > limit:
        return False
    prev2, prev = None, list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            if prev2 and i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[-1] <= limit


@lru_cache(maxsize=1)
def _index():
    """alias (word tuple) -> recipe ingredient names, and which aliases may be matched by a part of them."""
    from app.plan.nutrition import ingredients
    table = ingredients()
    exact, partial = {}, {}

    def add(alias_text, name, may_be_part):
        alias = norm(alias_text)
        if not alias:
            return
        exact.setdefault(alias, set()).add(name)
        if may_be_part:
            partial.setdefault(alias, set()).add(name)

    names = list(INGREDIENTS) + list(MIXES) + sorted(TRACE)
    for name in names:
        add(name, name, True)
        hi, te = LOCAL_NAMES.get(name, (None, None))
        for local in (hi, te):
            if local:
                add(local, name, False)  # whole names only: "బెంగళూరు వంకాయ" (chow chow) is not brinjal
        for synonym in SYNONYMS.get(name, []):
            add(synonym, name, True)
        entry = INGREDIENTS.get(name)
        if not entry:
            continue
        codes = entry[0] if isinstance(entry[0], tuple) else (entry[0],)
        for code in codes:
            food = table.get(code)
            if not food:
                continue
            add(food["name"], name, True)  # official IFCT name, e.g. "Brinjal - all varieties"
            for regional in (food.get("names") or {}).values():
                for part in re.split(r"[,/;()]", regional or ""):
                    add(part, name, False)  # regional names only as a whole: short words collide across languages
    return exact, partial


@dataclass(frozen=True)
class Avoid:
    text: str
    groups: frozenset
    ingredients: frozenset  # recipe ingredient names (also spice mixes and trace items)
    phrase: tuple  # the typed words, for dish names
    known: bool


def _group_of(phrase: tuple) -> set:
    return {g for g, words in GROUP_WORDS.items() for w in words if norm(w) == phrase}


@lru_cache(maxsize=512)
def resolve(text: str) -> Avoid:
    phrase = norm(text)
    if not phrase:
        return Avoid(text, frozenset(), frozenset(), phrase, False)
    exact, partial = _index()
    groups = _group_of(phrase)
    found = set(exact.get(phrase, set()))
    meaningful = not (len(phrase) == 1 and (phrase[0] in GENERIC or len(phrase[0]) < 3))
    if meaningful and not groups:
        for alias, ingr in partial.items():
            if len(alias) > len(phrase) and _contains(alias, phrase):
                found |= ingr
    if not found and not groups and len(phrase) == 1 and len(phrase[0]) >= 5:
        for alias, ingr in partial.items():  # one typo: "brinjall", "penut", "cashw" (not regional names)
            if len(alias) == 1 and _close(phrase[0], alias[0]):
                found |= ingr
        if not found:
            for g, words in GROUP_WORDS.items():
                if any(len(norm(w)) == 1 and _close(phrase[0], norm(w)[0]) for w in words):
                    groups.add(g)
    known = bool(groups or found or phrase in {norm(w) for w in NOT_USED} or _dish_named(phrase))
    return Avoid(text.strip(), frozenset(groups), frozenset(found), phrase, known)


@lru_cache(maxsize=1)
def _dish_texts() -> dict:
    """dish id -> (word tuples of its names, set of its ingredient names incl. mixes and trace items)."""
    from app.plan.catalog import catalog
    from app.plan.dish_names import NAMES as DISH_LOCAL
    out = {}
    for d in catalog().values():
        texts = [d["name"], *d.get("also_called", []), *(DISH_LOCAL.get(d["id"], {}) or {}).values(),
                 *(d.get("names") or {}).values()]
        ingr = {i["name"] for i in d["ingredients"]} | {n for i in d["ingredients"] for n, _ in expand(i["name"], i["grams"])}
        out[d["id"]] = (tuple(norm(t) for t in texts if t), frozenset(ingr))
    return out


def _dish_named(phrase: tuple) -> bool:
    return any(_contains(t, phrase) for texts, _ in _dish_texts().values() for t in texts)


def blocks_dish(dish: dict, avoid: Avoid) -> bool:
    if avoid.groups & set(dish["allergens"]):
        return True
    texts, ingr = _dish_texts()[dish["id"]]
    if avoid.ingredients & ingr:
        return True
    meaningful = not (len(avoid.phrase) == 1 and (avoid.phrase[0] in GENERIC or len(avoid.phrase[0]) < 3))
    return bool(avoid.phrase) and meaningful and any(_contains(t, avoid.phrase) for t in texts)


def ingredient_codes(names) -> set:
    """IFCT/USDA codes behind recipe ingredient names."""
    codes = set()
    for name in names:
        entry = INGREDIENTS.get(name)
        if entry:
            codes |= set(entry[0] if isinstance(entry[0], tuple) else (entry[0],))
    return codes


def blocks_food(food: dict, codes: set, allergens: set, avoid: Avoid) -> bool:
    """A food card (foods.json) against a typed allergy. codes and allergens are the card's ingredient codes and
    its full allergen set."""
    if avoid.groups & allergens:
        return True
    if ingredient_codes(avoid.ingredients) & codes:
        return True
    meaningful = not (len(avoid.phrase) == 1 and (avoid.phrase[0] in GENERIC or len(avoid.phrase[0]) < 3))
    if not (avoid.phrase and meaningful):
        return False
    names = [food.get("name") or "", food.get("hindi_name") or ""]
    return any(_contains(norm(part), avoid.phrase) for n in names for part in re.split(r"[/,()]", n))


def saved_report_conflicts(analysis: dict) -> dict:
    """A saved report checked against today's rules: suggested foods and saved plan dishes that its own profile
    (diet, meats, allergy groups, typed allergies) now excludes, and dishes no longer offered (beef and pork were
    removed). The lab results themselves are never changed."""
    from app.engine.recommender import FOODS_DATABASE
    from app.plan.engine import DIET_ALLOWS, food_facts
    profile = analysis.get("user_profile") or {}
    groups = set(profile.get("allergens") or [])
    typed = [resolve(w) for w in profile.get("custom_allergies") or [] if w and w.strip()]
    meats = set(profile.get("meats") or [])
    diet = profile.get("diet_type") or "veg"
    foods = {f["id"]: f for f in FOODS_DATABASE}
    found = []
    for plan in analysis.get("recommendations") or []:
        for item in plan.get("recommended_foods") or []:
            food = foods.get(item.get("id"))
            if food is None:
                continue
            codes, allergens, food_meats = food_facts(food)
            if (groups & allergens or (meats and food_meats - meats)
                    or any(blocks_food(food, codes, allergens, a) for a in typed)):
                found.append(item.get("name") or food["name"])
    dishes = catalog_dishes()
    allowed = DIET_ALLOWS.get(diet, DIET_ALLOWS["veg"])
    for day in ((analysis.get("diet_plan") or {}).get("days") or []):
        for items in (day.get("meals") or {}).values():
            for item in items:
                d = dishes.get(item.get("dish_id"))
                if (d is None or d["diet"] not in allowed or groups & set(d["allergens"])
                        or (meats and set(d["meat_types"]) - meats) or any(blocks_dish(d, a) for a in typed)):
                    found.append(item.get("name") or item.get("dish_id"))
    found = list(dict.fromkeys(found))
    return {"allergy_conflicts": found, "can_regenerate": bool(found)}


def catalog_dishes() -> dict:
    from app.plan.catalog import catalog
    return catalog()
