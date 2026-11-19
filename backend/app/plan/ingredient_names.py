"""The ingredient names dishes are written with, and the food each one means.

Every name points to an IFCT 2017 food code (or an X code added from USDA FoodData Central), together with words the
official food name must contain. A test checks every entry against ingredients.json, so a mistyped code cannot slip
through. A tuple of codes means the varieties are averaged in equal parts (for example the two ripe tomatoes in IFCT).

Approximations, all small and stated here:
- besan and roasted gram (putnalu) use chana dal: besan is ground chana dal, and roasting only removes a little water.
- rice flour uses raw milled rice; idli rava uses parboiled rice, which it is made from. Kerala matta rice is
  parboiled rice; IFCT has no separate entry for the red variety.
- ripe plantain (nendran, for pazham pori) uses IFCT's montham, the cooking banana in the tables.
- chilli powder uses dry red chillies, which it is ground from. Black salt (kala namak) is counted as salt.
- kabuli (white) chana comes from USDA (X019); IFCT lists only the brown desi chana.
- "oil" is refined sunflower oil, the most widely used cooking oil. Dishes made with groundnut, sesame or coconut oil
  name that oil, so nut and sesame allergies are flagged correctly.
TRACE ingredients are listed in recipes for completeness but have no IFCT entry and are used in amounts too small
to change any nutrient (a piece of cinnamon, a bay leaf, tea leaves, two pieces of kudampuli).
"""

INGREDIENTS = {
    # cereals and millets
    "rice": ("A015", "Rice, raw, milled"),
    "rice flour": ("A015", "Rice, raw, milled"),
    "brown rice": ("A013", "Rice, raw, brown"),
    "parboiled rice": ("A014", "Rice, parboiled"),
    "idli rava": ("A014", "Rice, parboiled"),
    "rice flakes": ("A011", "Rice, flakes"),
    "puffed rice": ("A012", "Rice, puffed"),
    "semolina": ("A022", "Wheat, semolina"),
    "wheat flour": ("A019", "Wheat flour, atta"),
    "refined wheat flour": ("A018", "Wheat flour, refined"),
    "vermicelli": ("A024", "Wheat, vermicelli, roasted"),
    "dalia": ("A021", "Wheat, bulgur"),
    "maize flour": ("A006", "Maize, dry"),
    "jowar flour": ("A005", "Jowar"),
    "bajra flour": ("A003", "Bajra"),
    "ragi flour": ("A010", "Ragi"),
    "little millet": ("A016", "Samai"),
    "tender corn": ("A007", "Maize, tender, local"),
    "sweet corn": ("A008", "Maize, tender, sweet"),
    "oats": ("X008", "Oats, rolled"),
    "whole wheat bread": ("X013", "Bread, whole wheat"),
    # pulses
    "toor dal": ("B021", "Red gram, dal"),
    "moong dal": ("B010", "Green gram, dal"),
    "whole moong": ("B011", "Green gram, whole"),
    "urad dal": ("B003", "Black gram, dal"),
    "chana dal": ("B001", "Bengal gram, dal"),
    "besan": ("B001", "Bengal gram, dal"),
    "roasted gram": ("B001", "Bengal gram, dal"),
    "black chana": ("B002", "Bengal gram, whole"),
    "kabuli chana": ("X019", "Chickpeas, kabuli"),
    "whole urad": ("B004", "Black gram, whole"),
    "horse gram": ("B012", "Horse gram, whole"),
    "cowpea": ("B005", "Cowpea, brown"),
    "white cowpea": ("B006", "Cowpea, white"),
    "masoor dal": ("B013", "Lentil, dal"),
    "rajma": ("B020", "Rajmah, red"),
    "moth bean": ("B016", "Moth bean"),
    "dry peas": ("B017", "Peas, dry"),
    # vegetables
    "onion": ("G017", "Onion, big"),
    "small onion": ("G018", "Onion, small"),
    "spring onion": ("D058", "Onion, stalk"),
    "tomato": (("D075", "D076"), "Tomato, ripe"),
    "potato": (("F006", "F007"), "Potato, brown skin"),
    "brinjal": ("D031", "Brinjal"),
    "okra": ("D056", "Ladies finger"),
    "ivy gourd": (("D054", "D055"), "Kovai"),
    "bitter gourd": (("D004", "D005", "D006"), "Bitter gourd"),
    "bottle gourd": (("D007", "D008", "D009"), "Bottle gourd"),
    "ridge gourd": (("D068", "D069"), "Ridge gourd"),
    "snake gourd": (("D070", "D071", "D072"), "Snake gourd"),
    "ash gourd": ("D001", "Ash gourd"),
    "pumpkin": ("D066", "Pumpkin"),
    "cabbage": ("C015", "Cabbage, green"),
    "cauliflower": ("D036", "Cauliflower"),
    "carrot": ("F002", "Carrot"),
    "beetroot": ("F001", "Beetroot"),
    "french beans": (("D049", "D050"), "French beans"),
    "cluster beans": ("D039", "Cluster beans"),
    "field beans": (("D047", "D048"), "Field beans, tender"),
    "drumstick": ("D046", "Drumstick"),
    "colocasia": ("F004", "Colocasia"),
    "elephant yam": ("F017", "Yam, elephant"),
    "tapioca": ("F015", "Tapioca"),
    "raw banana": ("D063", "Plantain, green"),
    "ripe plantain": ("E009", "Banana, ripe, montham"),
    "radish": ("F010", "Radish"),
    "capsicum": ("D033", "Capsicum, green"),
    "chow chow": ("D038", "Cho-cho-marrow"),
    "knol khol": ("D053", "Knol"),
    "cucumber": (("D043", "D044"), "Cucumber, green"),
    "yellow cucumber": ("D045", "Cucumber, orange, round"),
    "raw mango": ("D057", "Mango, green, raw"),
    "green peas": ("D061", "Peas, fresh"),
    "mushroom": ("J001", "Button mushroom, fresh"),
    "tinda": ("D073", "Tinda"),
    "parwal": ("D060", "Parwar"),
    "sweet potato": (("F013", "F014"), "Sweet potato"),
    "bamboo shoot": ("D002", "Bamboo shoot"),
    "sago": ("X011", "Sago"),
    # leafy vegetables
    "spinach": ("C033", "Spinach"),
    "amaranth leaves": (("C002", "C003", "C004"), "Amaranth leaves"),
    "fenugreek leaves": ("C020", "Fenugreek leaves"),
    "gongura": (("C022", "C023"), "Gogu leaves"),
    "ponnaganti": ("C029", "Ponnaganni"),
    "drumstick leaves": ("C019", "Drumstick leaves"),
    "mustard leaves": ("C026", "Mustard leaves"),
    "bathua": ("C008", "Bathua leaves"),
    # herbs and spices
    "coriander leaves": ("G009", "Coriander leaves"),
    "curry leaves": ("G010", "Curry leaves"),
    "mint leaves": ("G016", "Mint leaves"),
    "ginger": ("G014", "Ginger, fresh"),
    "garlic": ("G011", "Garlic"),
    "green chilli": ("G008", "Chillies, green"),
    "dry red chilli": ("G022", "Chillies, red"),
    "chilli powder": ("G022", "Chillies, red"),
    "turmeric": ("G033", "Turmeric powder"),
    "cumin seeds": ("G025", "Cumin seeds"),
    "mustard seeds": ("H013", "Mustard seeds"),
    "fenugreek seeds": ("G026", "Fenugreek seeds"),
    "asafoetida": ("G019", "Asafoetida"),
    "black pepper": ("G031", "Pepper, black"),
    "coriander seeds": ("G024", "Coriander seeds"),
    "coriander powder": ("G024", "Coriander seeds"),
    "cloves": ("G023", "Cloves"),
    "cardamom": ("G020", "Cardamom"),
    "poppy seeds": ("G032", "Poppy seeds"),
    "ajwain": ("G029", "Omum"),
    # souring, sweetening, salt
    "tamarind": ("E064", "Tamarind, pulp"),
    "lemon juice": ("E033", "Lemon, juice"),
    "jaggery": ("I001", "Jaggery"),
    "sugar": ("X003", "Sugar"),
    "salt": ("X004", "Salt"),
    "black salt": ("X004", "Salt"),
    "honey": ("X005", "Honey"),
    # coconut, nuts and seeds
    "fresh coconut": ("H007", "Coconut, kernel, fresh"),
    "dry coconut": ("H006", "Coconut, kernel, dry"),
    "coconut milk": ("X009", "Coconut milk"),
    "coconut water": ("K002", "Coconut water"),
    "peanuts": ("H012", "Ground nut"),
    "sesame seeds": ("H011", "Gingelly seeds"),
    "cashew": ("H005", "Cashew nut"),
    "almonds": ("H001", "Almond"),
    "pistachios": ("H018", "Pistachio"),
    "raisins": ("E057", "Raisins"),
    # fats
    "oil": ("T012", "Sunflower oil"),
    "groundnut oil": ("T005", "Groundnut oil"),
    "sesame oil": ("T004", "Gingelly oil"),
    "coconut oil": ("T001", "Coconut oil"),
    "mustard oil": ("T006", "Mustard oil"),
    "ghee": ("T013", "Ghee"),
    "butter": ("X002", "Butter"),
    # milk and milk products
    "milk": ("L002", "Milk, whole, Cow"),
    "fortified milk": ("X018", "Milk, fortified"),
    "curd": ("X001", "Curd"),
    "buttermilk": ("X016", "Buttermilk"),
    "paneer": ("L003", "Paneer"),
    "khoa": ("L004", "Khoa"),
    "fresh cream": ("X010", "Fresh cream"),
    "soya chunks": ("X007", "Soya chunks"),
    "cornflour": ("X012", "Cornflour"),
    # eggs, meat, fish
    "egg": ("M001", "Egg, poultry, whole, raw"),
    "chicken": (("N001", "N002", "N003", "N004"), "Chicken, poultry"),
    "country chicken": (("N007", "N008", "N009", "N010"), "Country hen"),
    "mutton": (("O001", "O002", "O003"), "Goat"),
    "beef": (("O025", "O027"), "Beef"),
    "chicken liver": ("N005", "chicken, liver"),
    "mutton liver": ("O008", "Goat, liver"),
    "freshwater fish": (("S006", "S002"), ("Rohu", "Catla")),
    "seer fish": ("P087", "Vanjaram"),
    "sardine": ("P071", "Sardine"),
    "mackerel": ("P034", "Mackerel"),
    "anchovy": ("P003", "Anchovy"),
    "hilsa": ("P017", "Hilsa"),
    "pork": (("O048", "O049"), "Pork"),
    "prawns": (("S008", "S009"), "Prawns"),
    # fruits
    "banana": ("E012", "Banana, ripe, robusta"),
    "guava": ("E028", "Guava"),
    "apple": ("E001", "Apple"),
    "orange": ("E047", "Orange, pulp"),
    "papaya": ("E049", "Papaya, ripe"),
    "watermelon": (("E065", "E066"), "Water melon"),
    "pomegranate": ("E055", "Pomegranate"),
    "sapota": ("E060", "Sapota"),
    "mango": ("E036", "Mango, ripe"),
    "grapes": ("E022", "Grapes"),
}

TRACE = {"cinnamon", "bay leaf", "tea leaves", "coffee powder", "fennel seeds", "star anise", "kudampuli",
         "dill leaves", "saffron", "yeast", "kasuri methi", "amchur", "nutmeg", "kokum",
         "panch phoron", "nigella"}

# Ground mixes, as the share of each ingredient in a typical home recipe. Used a gram or two at a time.
MIXES = {
    "ginger-garlic paste": [("ginger", 0.5), ("garlic", 0.5)],
    "garam masala": [("coriander seeds", 0.35), ("cumin seeds", 0.25), ("black pepper", 0.15), ("cardamom", 0.10),
                     ("cloves", 0.10), ("cinnamon", 0.05)],
    "sambar powder": [("coriander seeds", 0.40), ("dry red chilli", 0.30), ("chana dal", 0.10), ("toor dal", 0.05),
                      ("cumin seeds", 0.05), ("fenugreek seeds", 0.05), ("black pepper", 0.05)],
    "rasam powder": [("coriander seeds", 0.40), ("black pepper", 0.20), ("cumin seeds", 0.20),
                     ("dry red chilli", 0.10), ("toor dal", 0.10)],
    # chaat masala is about 40% salt (black salt), which matters for sodium even at a gram
    "chaat masala": [("black salt", 0.40), ("cumin seeds", 0.25), ("coriander seeds", 0.10), ("black pepper", 0.05),
                     ("dry red chilli", 0.05), ("amchur", 0.15)],
}


def expand(name: str, grams: float) -> list:
    """A recipe line as (ingredient name, grams) pairs: mixes become their parts, trace items are dropped."""
    if name in MIXES:
        return [part for sub, share in MIXES[name] for part in expand(sub, grams * share)]
    if name in TRACE:
        return []
    return [(name, grams)]
