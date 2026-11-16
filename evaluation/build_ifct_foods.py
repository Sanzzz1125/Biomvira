#!/usr/bin/env python3
"""Add common Indian foods from the Indian Food Composition Tables 2017 (IFCT, ICMR-NIN) to foods.json.

Source data: the open `ifct2017` dataset (compositions/index.csv), which republishes IFCT 2017 values per 100 g of
raw edible portion. Usage:

    python evaluation/build_ifct_foods.py <path/to/ifct2017/compositions/index.csv>

Re-running replaces every previously generated (ifct_) entry, so the script can be run again safely.

Rules:
* Only foods not already in foods.json are added (the curated entries keep their own values and tips).
* Nutrients are scaled from per-100 g raw values to the stated raw serving. Values IFCT does not report
  (vitamin B12, reliable vitamin D for plant foods) are left out rather than set to zero.
* Tags come from the data: high fibre = at least 6 g dietary fibre per 100 g; healthy fats = at least 5 g fat per 100 g
  with mono + polyunsaturated fat at least twice the saturated fat; omega-3 = at least 1 g ALA or 0.2 g EPA+DHA per 100 g.
  "Low GI" is only given to food groups that are consistently low-glycaemic (pulses, leafy and non-starchy vegetables,
  nuts and seeds) and to a few well-studied foods (barley, apple, orange, pear).
"""
import csv
import json
import re
import sys
from pathlib import Path

FOODS = Path(__file__).resolve().parents[1] / "backend" / "app" / "data" / "foods.json"

ALL_DIETS = ["veg", "vegan", "eggetarian", "non_veg"]
GROUPS = {  # IFCT group -> (category, diets, allergens, default serving g, serving label, low_gi)
    "Cereals and Millets": ("Millets & Grains", ALL_DIETS, [], 50, "50g raw", False),
    "Grain Legumes": ("Pulses & Legumes", ALL_DIETS, [], 30, "30g raw (about 1 katori cooked)", True),
    "Green Leafy Vegetables": ("Green Leafy Vegetables", ALL_DIETS, [], 100, "100g raw (about 1 cup chopped)", True),
    "Other Vegetables": ("Vegetables", ALL_DIETS, [], 100, "100g raw", True),
    "Roots and Tubers": ("Root Vegetables", ALL_DIETS, [], 100, "100g raw", False),
    "Fruits": ("Fruits & Catalysts", ALL_DIETS, [], 100, "100g", False),
    "Condiments and Spices": ("Herbs & Condiments", ALL_DIETS, [], 5, "5g", False),
    "Nuts and Oil Seeds": ("Seeds & Nuts", ALL_DIETS, [], 20, "20g (a small handful)", True),
    "Milk and Milk Products": ("Dairy", ["veg", "eggetarian", "non_veg"], ["dairy"], 200, "200ml (1 glass)", False),
    "Egg and Egg Products": ("Eggs & Poultry", ["eggetarian", "non_veg"], ["eggs"], 50, "1 egg (50g)", False),
    "Poultry": ("Eggs & Poultry", ["non_veg"], [], 100, "100g raw", False),
    "Animal Meat": ("Red Meat", ["non_veg"], [], 100, "100g raw", False),
    "Marine Fish": ("Seafood & Fish", ["non_veg"], ["seafood"], 100, "100g raw", False),
    "Marine Shellfish": ("Seafood & Fish", ["non_veg"], ["seafood"], 100, "100g raw", False),
    "Fresh Water Fish and Shellfish": ("Seafood & Fish", ["non_veg"], ["seafood"], 100, "100g raw", False),
    "Mushrooms": ("Vegetables", ALL_DIETS, [], 100, "100g raw", True),
}

# code -> (display name, serving override (g, label) or None, extra allergens, low-GI override)
PICK = {
    # cereals and millets
    "A001": ("Amaranth Seed / Rajgira", None, [], None), "A004": ("Barley / Jau", None, ["gluten"], True),
    "A006": ("Maize, Dry / Makka", None, [], None), "A011": ("Rice Flakes / Poha", None, [], None),
    "A013": ("Brown Rice", None, [], None), "A014": ("Parboiled Rice", None, [], None), "A015": ("White Rice (Raw, Milled)", None, [], None),
    "A017": ("Kodo Millet / Varagu", None, [], None), "A019": ("Whole Wheat Flour / Atta", None, ["gluten"], None),
    "A020": ("Whole Wheat", None, ["gluten"], None), "A021": ("Broken Wheat / Dalia", None, ["gluten"], None),
    "A022": ("Semolina / Rava / Sooji", None, ["gluten"], None),
    # pulses and legumes
    "B002": ("Whole Bengal Gram / Kala Chana", None, [], None), "B003": ("Split Black Gram / Urad Dal", None, [], None),
    "B010": ("Split Green Gram / Moong Dal", None, [], None), "B011": ("Whole Green Gram / Moong", None, [], None),
    "B013": ("Red Lentil Dal / Masoor Dal", None, [], None), "B014": ("Whole Brown Lentil / Sabut Masoor", None, [], None),
    "B017": ("Dried Peas / Sukhe Matar", None, [], None),
    "B021": ("Split Red Gram / Toor Dal", None, [], None), "B022": ("Whole Red Gram / Arhar", None, [], None),
    "B023": ("Rice Bean / Naurangi Dal", None, [], None),
    # green leafy vegetables
    "C001": ("Agathi Leaves", None, [], None), "C007": ("Malabar Spinach / Poi Saag", None, [], None),
    "C008": ("Bathua Leaves", None, [], None), "C009": ("Beetroot Greens", None, [], None),
    "C015": ("Green Cabbage / Patta Gobhi", None, [], None), "C018": ("Colocasia Leaves / Arbi Patta", None, [], None),
    "C021": ("Garden Cress Greens", None, [], None), "C022": ("Gongura / Gogu Leaves", None, [], None),
    "C026": ("Mustard Greens / Sarson ka Saag", None, [], None), "C029": ("Ponnaganni Leaves", None, [], None),
    "C031": ("Radish Leaves / Mooli Patta", None, [], None), "C017": ("Cauliflower Greens", None, [], None),
    "C030": ("Tender Pumpkin Leaves", None, [], None), "C034": ("Tender Tamarind Leaves", None, [], None),
    # other vegetables
    "D001": ("Ash Gourd / Petha", None, [], None), "D031": ("Brinjal / Baingan", None, [], None),
    "D033": ("Green Capsicum / Shimla Mirch", None, [], None), "D036": ("Cauliflower / Phool Gobhi", None, [], None),
    "D039": ("Cluster Beans / Gawar", None, [], None), "D043": ("Cucumber / Kheera", None, [], None),
    "D049": ("French Beans", None, [], None), "D054": ("Ivy Gourd / Kundru / Dondakaya", None, [], None),
    "D056": ("Ladies Finger / Bhindi", None, [], None), "D060": ("Pointed Gourd / Parwal", None, [], None),
    "D061": ("Fresh Green Peas / Matar", None, [], False), "D062": ("Banana Flower / Kele ka Phool", None, [], None),
    "D064": ("Banana Stem", None, [], None), "D066": ("Pumpkin / Kaddu", None, [], None),
    "D068": ("Ridge Gourd / Turai", None, [], None), "D070": ("Snake Gourd / Chichinda", None, [], None),
    "D073": ("Round Gourd / Tinda", None, [], None), "D076": ("Tomato / Tamatar", None, [], None),
    "D032": ("Broad Beans / Sem", None, [], None), "D053": ("Knol-Khol / Ganth Gobhi", None, [], None),
    # roots and tubers
    "F002": ("Carrot / Gajar", None, [], None), "F004": ("Colocasia / Arbi", None, [], None),
    "F006": ("Potato / Aloo", None, [], None), "F010": ("White Radish / Mooli", None, [], None),
    "F015": ("Tapioca / Cassava", None, [], None), "F017": ("Elephant Foot Yam / Suran", None, [], None),
    # fruits
    "E001": ("Apple / Seb", None, [], True), "E008": ("Bael Fruit", None, [], None), "E012": ("Banana / Kela (Ripe)", None, [], None),
    "E016": ("Custard Apple / Sitaphal", None, [], None), "E025": ("Black Grapes / Angoor", None, [], None),
    "E030": ("Ripe Jackfruit / Kathal", None, [], None),
    "E031": ("Jamun / Black Plum", None, [], None), "E036": ("Mango / Aam (Ripe)", None, [], None),
    "E047": ("Orange / Santra", None, [], True), "E051": ("Pear / Nashpati", None, [], True), "E052": ("Phalsa", None, [], None),
    "E053": ("Pineapple / Ananas", None, [], None), "E055": ("Pomegranate / Anar", None, [], None),
    "E060": ("Sapota / Chikoo", None, [], None), "E065": ("Watermelon / Tarbooz", None, [], None),
    "E068": ("Indian Jujube / Ber", None, [], None), "E067": ("Wood Apple / Kaitha", None, [], None),
    "E020": ("Fresh Fig / Anjeer", None, [], None),
    # herbs and spices
    "G009": ("Coriander Leaves / Dhaniya Patta", (10, "10g (a handful)"), [], None),
    "G016": ("Mint Leaves / Pudina", (10, "10g (a handful)"), [], None), "G011": ("Garlic / Lahsun", None, [], None),
    "G014": ("Fresh Ginger / Adrak", None, [], None), "G017": ("Onion / Pyaz", (50, "50g (1 small onion)"), [], None),
    "G024": ("Coriander Seeds / Dhaniya", None, [], None), "G025": ("Cumin Seeds / Jeera", None, [], None),
    "G026": ("Fenugreek Seeds / Methi Dana", (10, "10g (2 teaspoons)"), [], None), "G029": ("Ajwain / Carom Seeds", None, [], None),
    "G031": ("Black Pepper / Kali Mirch", None, [], None), "G032": ("Poppy Seeds / Khus Khus", (10, "10g (2 teaspoons)"), [], None),
    "G033": ("Turmeric Powder / Haldi", None, [], None),
    # nuts and oil seeds
    "H006": ("Dry Coconut / Kopra", None, [], None), "H007": ("Fresh Coconut", (30, "30g (2 tablespoons grated)"), [], None),
    "H012": ("Groundnut / Peanut", None, ["nuts"], None), "H013": ("Mustard Seeds / Rai", (10, "10g (2 teaspoons)"), [], None),
    "H015": ("Niger Seeds / Ramtil", (10, "10g (1 tablespoon)"), [], None), "H018": ("Pistachio / Pista", None, ["nuts"], None),
    "H021": ("Walnut / Akhrot", None, ["nuts"], None), "H019": ("Safflower Seeds / Kusum", (10, "10g (1 tablespoon)"), [], None),
    # dairy
    "L001": ("Buffalo Milk (Whole)", None, [], None), "L004": ("Khoa / Mawa", (30, "30g"), [], None),
    # eggs
    "M009": ("Country Hen Egg (Boiled)", None, [], None), "M011": ("Duck Egg (Boiled)", None, [], None),
    # poultry and meat
    "N001": ("Chicken Leg (Skinless)", None, [], None), "N006": ("Chicken Gizzard", None, [], None),
    "O011": ("Goat Kidney", (50, "50g raw"), [], None),
    # fish and shellfish
    "P003": ("Anchovy / Nethili", None, [], None), "P007": ("Bombay Duck / Bombil", None, [], None),
    "P026": ("Pearl Spot / Karimeen", None, [], None), "P039": ("Mullet", None, [], None),
    "P055": ("Black Pomfret", None, [], None), "P057": ("White Pomfret", None, [], None),
    "P060": ("Queen Fish", None, [], None), "P065": ("Red Snapper", None, [], None), "P068": ("Salmon / Rawas", None, [], None),
    "P071": ("Sardine / Mathi / Tarli", None, [], None), "P084": ("Tuna", None, [], None),
    "P087": ("Seer Fish / Vanjaram / Surmai", None, [], None), "P083": ("Tilapia", None, [], None),
    "Q001": ("Crab / Kekda", None, [], None), "S002": ("Catla", None, [], None), "S005": ("Pangas / Basa", None, [], None),
}

TIPS = {
    "Millets & Grains": "Use as roti, khichdi, upma or porridge in place of polished rice or maida.",
    "Pulses & Legumes": "Soak overnight and pressure-cook as dal, sundal or usal, or sprout it; add lemon for better iron absorption.",
    "Green Leafy Vegetables": "Cook lightly as saag, palya or poriyal, or add to dal; finish with a squeeze of lemon.",
    "Vegetables": "Cook as a dry sabzi, curry or sambar with little oil.",
    "Root Vegetables": "Boil, roast or cook as a sabzi; keep portions moderate if watching blood sugar.",
    "Fruits & Catalysts": "Eat whole and fresh as a snack rather than as juice.",
    "Herbs & Condiments": "Use daily in tempering, chutneys and masalas.",
    "Seeds & Nuts": "Eat a small handful, or add to chutneys, laddoos or salads.",
    "Dairy": "Have as part of meals; choose plain, unsweetened forms.",
    "Eggs & Poultry": "Boil, grill or cook in a light curry with vegetables.",
    "Red Meat": "Prefer lean cuts cooked as a curry or grilled, with little oil.",
    "Organ Meats": "Cook thoroughly; a small portion once or twice a week is enough.",
    "Seafood & Fish": "Grill, steam or cook in a light curry rather than deep-frying.",
}
NOTES = {
    "Pulses & Legumes": "Pulses give plant protein and fibre; pairing with cereals makes a complete protein.",
    "Green Leafy Vegetables": "Pair with vitamin C (lemon, amla, tomato) to help the body absorb plant iron.",
    "Millets & Grains": "Whole and less-polished grains keep more of their fibre and minerals.",
    "Seafood & Fish": "Fish provides easily absorbed (haem) iron and high-quality protein.",
    "Red Meat": "Meat provides easily absorbed (haem) iron.",
    "Organ Meats": "Organ meats provide easily absorbed (haem) iron.",
}


# Protein and purine tags. Generated foods get them from IFCT protein values and their food group; the hand-curated
# foods get them here. Low purine follows common gout guidance: dairy, eggs, vegetables, fruit, grains, nuts and seeds are
# low; organ meats, red meat, seafood, yeast and (conservatively) pulses, soy and mushrooms are left out.
LOW_PURINE_CATEGORIES = {"Dairy", "Fruits & Catalysts", "Vegetables", "Root Vegetables", "Millets & Grains",
                         "Green Leafy Vegetables", "Seeds & Nuts", "Dried Fruits"}
# Approximate protein (g) per stated serving, from standard food tables. Used only to order the protein plan; the
# app does not display these figures.
CURATED_HIGH_PROTEIN = {
    "paneer_cottage_cheese": 18, "curd_yogurt": 7, "cow_milk_whole": 8, "whole_egg_boiled": 13, "chicken_breast": 45,
    "chicken_liver": 24, "mutton_goat_meat": 25, "rohu_freshwater_fish": 25, "mackerel_bangda": 23, "hilsa_fish_ilish": 22,
    "prawn_shrimp": 24, "mutton_liver": 26, "roasted_chana": 11, "rajma_kidney_beans": 13, "chana_dal": 13,
    "black_urad_dal": 12, "horse_gram_kulthi": 12, "moth_beans_matki": 11, "soybean_cooked": 25,
    "lobia_black_eyed_peas": 12, "tofu_firm": 15, "tempeh": 19, "fortified_soy_milk": 8, "fortified_milk_fssai": 8,
    "pumpkin_seeds": 9, "sunflower_seeds": 6,
}


def tag_curated(food):
    tags = [t for t in food.get("tags", []) if t not in ("high_protein", "low_purine")]
    if food["id"] in CURATED_HIGH_PROTEIN:
        tags.append("high_protein")
        food["protein_rank_g"] = CURATED_HIGH_PROTEIN[food["id"]]
    if (food["category"] in LOW_PURINE_CATEGORIES or food["id"] == "whole_egg_boiled") and "mushroom" not in food["id"]:
        tags.append("low_purine")
    food["tags"] = tags


def num(row, key):
    try:
        return float(row.get(key) or 0)
    except ValueError:
        return 0.0


def regional_names(lang):
    parts = {p.split(".", 1)[0].strip(): p.split(".", 1)[1].strip(" .") for p in lang.split(";") if "." in p}
    names = [parts.get("H"), parts.get("Tel")]
    names = [n.split(",")[0].strip().title() for n in names if n and n.split(",")[0].strip()]
    return " / ".join(dict.fromkeys(names)) or None


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def build(csv_path):
    data = json.loads(FOODS.read_text(encoding="utf-8"))
    data["foods"] = [f for f in data["foods"] if not f["id"].startswith("ifct_")]  # rebuild cleanly on re-run
    for food in data["foods"]:
        tag_curated(food)
    existing_ids = {f["id"] for f in data["foods"]}
    rows = {r["code"]: r for r in csv.DictReader(open(csv_path, encoding="utf-8"))}
    added = []
    for code, (name, serving, extra_allergens, low_gi_override) in PICK.items():
        row = rows[code]
        category, diets, allergens, grams, label, group_low_gi = GROUPS[row["grup"]]
        if serving:
            grams, label = serving
        if row["grup"] == "Animal Meat" and re.search(r"liver|kidney", row["name"], re.I):
            category = "Organ Meats"
        food_id = f"ifct_{code.lower()}_{slug(name.split('/')[0])}"
        if food_id in existing_ids:
            continue
        per = lambda key, scale: round(num(row, key) * scale * grams / 100, 1)
        nutrients = {
            "iron_mg": per("fe", 1000), "calcium_mg": per("ca", 1000), "folate_mcg": per("folsum", 1e6),
            "vitamin_c_mg": per("vitc", 1000),
        }
        fat, sat = num(row, "fatce"), num(row, "fasat")
        unsat = num(row, "fams") + num(row, "fapu")
        tags = []
        # Spices are eaten in teaspoons, and fats that are mostly saturated (coconut) should not be pushed
        # for blood sugar or cholesterol, so neither gets tags.
        if row["grup"] == "Condiments and Spices" or (fat >= 5 and sat >= unsat):
            low_gi_override = False
        low_gi = group_low_gi if low_gi_override is None else low_gi_override
        if low_gi and row["grup"] not in ("Roots and Tubers",):
            tags.append("low_gi")
        skip = row["grup"] == "Condiments and Spices" or (fat >= 5 and sat >= unsat)
        if not skip and num(row, "fibtg") >= 6:
            tags.append("high_fibre")
        # Eggs carry dietary cholesterol, so they are not offered as a "healthy fat" for blood-fat plans.
        if not skip and row["grup"] != "Egg and Egg Products" and fat >= 5 and sat > 0 and unsat >= 2 * sat:
            tags.append("heart_healthy_fat")
        if not skip and num(row, "f18d3n3") >= 1.0 or (num(row, "f20d5n3") + num(row, "f22d6n3")) >= 0.2:
            tags.append("omega3")
        protein = num(row, "protcnt")
        if row["grup"] != "Condiments and Spices" and (protein * grams / 100 >= 6 or protein >= 20):
            tags.append("high_protein")
        if (category in LOW_PURINE_CATEGORIES or row["grup"] == "Egg and Egg Products") and row["grup"] != "Condiments and Spices":
            tags.append("low_purine")
        nutrients["protein_g"] = round(protein * grams / 100, 1)
        added.append({"protein_rank_g": nutrients["protein_g"],
            "id": food_id, "name": name, "hindi_name": regional_names(row.get("lang", "")), "category": category,
            "diet_type": diets, "allergens": sorted(set(allergens + extra_allergens)), "serving_size": label,
            "nutrients": nutrients, "synergies": [NOTES[category]] if category in NOTES else [],
            "tip": TIPS[category], "tags": tags, "source": f"IFCT 2017 ({code}: {row['name']})",
        })
    data["foods"] += added
    FOODS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return added


if __name__ == "__main__":
    new = build(sys.argv[1])
    print(f"added {len(new)} foods; foods.json now has", len(json.loads(FOODS.read_text())["foods"]))
