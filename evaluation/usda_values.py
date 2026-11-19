"""Add vitamin B12 and vitamin D to the IFCT ingredient table, and add common kitchen ingredients IFCT does not list.

Usage: python -I usda_values.py <USDA SR Legacy csv folder> <ingredients.json>   (updates the file in place)

Source: USDA FoodData Central, SR Legacy (April 2018), public domain (US government work).
IFCT 2017 has no vitamin B12, and its vitamin D values are not used (see build_ingredients.py), so:
- plant foods get 0 for both (they contain none naturally), except mushrooms, which are matched to USDA;
- animal foods are matched to a USDA food, with the quality of the match recorded:
    exact        the same food (for example hen's egg, whole, raw)
    similar      the same species family or a close equivalent (for example pomfret -> butterfish, paneer -> ricotta)
    approximate  no close match; the median of comparable foods is used. The plan engine counts half of an
                 approximate value, so a plan never relies on an uncertain number.
Vitamin D varies widely even within one species (wild against farmed fish, sun against lamp for mushrooms), so it is
listed in "uncertain" for every fish without an exact match and for UV- or sun-exposed mushrooms; approximate foods list
both B12 and vitamin D. The plan engine counts an uncertain value at half.
Kitchen ingredients missing from IFCT (curd, butter, sugar, salt and so on) are added with full USDA profiles.
USDA carbohydrate includes fibre; it is converted to available carbohydrate (minus fibre) to match IFCT.
"""
import csv
import json
import statistics
import sys
from pathlib import Path

NBR = {"energy_kcal": "208", "protein_g": "203", "fat_g": "204", "carbs_total_g": "205", "fibre_g": "291",
       "sugars_g": "269", "saturated_fat_g": "606", "cholesterol_mg": "601", "sodium_mg": "307", "potassium_mg": "306",
       "calcium_mg": "301", "iron_mg": "303", "zinc_mg": "309", "magnesium_mg": "304", "phosphorus_mg": "305",
       "folate_ug": "417", "vitamin_c_mg": "401", "vitamin_d_ug": "328", "vitamin_b12_ug": "418"}

E, S = "exact", "similar"
# IFCT code -> (USDA fdc_id, match quality)
MATCHES = {
    # milk and milk products
    "L001": ("171280", E), "L002": ("172217", E), "L003": ("170851", S), "T013": ("171314", E),
    # eggs
    "M001": ("171287", E), "M008": ("171287", E), "M004": ("173424", E), "M009": ("173424", E), "M007": ("173424", S),
    "M010": ("173424", S), "M002": ("172183", E), "M005": ("172183", E), "M003": ("172184", E), "M006": ("172184", E),
    "M011": ("172189", E), "M012": ("172189", E), "M013": ("172189", S), "M014": ("172191", E), "M015": ("172191", E),
    # poultry
    "N001": ("173619", E), "N002": ("173627", E), "N003": ("171077", E), "N004": ("173632", E), "N005": ("171060", E),
    "N006": ("171456", E), "N007": ("172378", E), "N008": ("172378", S), "N009": ("171077", S), "N010": ("173632", S),
    "N011": ("172410", E), "N012": ("172832", S), "N013": ("174471", E), "N014": ("171079", E), "N015": ("172419", E),
    "N016": ("171493", E), "N017": ("171493", S), "N018": ("171093", E), "N019": ("171132", E),
    # goat and sheep: cuts to goat; organs to lamb variety meats
    "O001": ("175303", E), "O002": ("175303", E), "O003": ("175303", E), "O014": ("175303", S), "O015": ("175303", S),
    "O016": ("175303", S), "O004": ("172525", S), "O017": ("172525", S), "O005": ("174366", S), "O018": ("174366", S),
    "O006": ("174359", S), "O019": ("174359", S), "O007": ("172527", S), "O020": ("172527", S), "O008": ("172531", S),
    "O021": ("172531", S), "O009": ("170599", S), "O022": ("170599", S), "O010": ("174364", S), "O023": ("174364", S),
    "O011": ("174354", S), "O024": ("174354", S),
    # beef, mithun, calf
    "O025": ("168742", S), "O026": ("168642", S), "O027": ("168742", S), "O045": ("168742", S), "O046": ("168642", S),
    "O047": ("168742", S), "O028": ("168622", E), "O029": ("170196", E), "O030": ("168628", E), "O031": ("168625", E),
    "O032": ("169451", E), "O033": ("170599", E), "O034": ("169454", E), "O035": ("169449", E),
    "O036": ("175280", E), "O037": ("173826", S), "O038": ("175269", E), "O042": ("172534", E), "O039": ("168622", S),
    "O040": ("170196", S), "O041": ("168625", S), "O043": ("169454", S), "O044": ("169449", S),
    # pork
    "O048": ("167845", E), "O049": ("167829", E), "O050": ("167816", E), "O051": ("167864", E), "O052": ("168267", E),
    "O053": ("167862", E), "O054": ("167867", E), "O055": ("167865", E), "O056": ("168270", E), "O057": ("167867", S),
    # hare and rabbit
    "O058": ("172521", S), "O059": ("172521", S), "O060": ("172521", S), "O061": ("172521", E), "O062": ("172521", E), "O063": ("172521", E),
    # fresh water fish and shellfish
    "S001": ("174186", S), "S002": ("171952", S), "S003": ("174193", S), "S004": ("171952", S), "S005": ("174186", S),
    "S006": ("171952", S), "S007": ("174204", S), "S008": ("174210", S), "S009": ("174210", S), "S010": ("174210", S),
    # marine shellfish and mollusks
    "Q001": ("174204", S), "Q002": ("174204", S), "Q005": ("174204", S), "Q003": ("174208", S), "Q004": ("174208", S),
    "Q006": ("171978", S), "Q007": ("174210", S), "Q008": ("174210", S), "R001": ("174214", S), "R002": ("174214", S),
    "R003": ("174218", E), "R004": ("174223", S), "R005": ("174223", S), "R006": ("174223", S), "R007": ("174223", S),
    # mushrooms
    "J001": ("169251", E), "J003": ("169242", E), "J004": ("168436", S),
}
# Marine fish matched by name (IFCT name -> fdc_id, quality); every other marine fish is "approximate".
MARINE_BY_NAME = {
    "Mackerel": ("173673", S), "Sardine": ("175140", S), "Tuna": ("175159", S), "Tuna, striped": ("175156", E),
    "Hilsa": ("173696", S), "Anchovy": ("174182", S), "Pomfret, black": ("171951", S), "Pomfret, white": ("171951", S),
    "Pomfret, snub nose": ("171951", S), "Mullet": ("175123", S), "Red snapper": ("173698", S),
    "Red snapper, small": ("173698", S), "Black snapper": ("173698", S), "Sole fish": ("174196", S),
    "Shark": ("173697", S), "Shark, hammer head": ("173697", S), "Shark, spotted": ("173697", S),
    "Whale shark": ("173697", S), "Milk fish": ("173675", E), "Tilapia": ("175176", E), "Silver carp": ("171952", S),
    "Cat fish": ("174186", S), "Vanjaram": ("173673", S),
}
# Kitchen ingredients IFCT does not list: (code, name, fdc_id, diet, animal source, allergens, Hindi, Telugu)
EXTRA = [
    ("X001", "Curd (dahi), whole milk", "171284", "vegetarian", "dairy", ["dairy"], "Dahi", "Perugu"),
    ("X002", "Butter", "173410", "vegetarian", "dairy", ["dairy"], "Makkhan", "Venna"),
    ("X003", "Sugar, white", "169655", "vegan", "none", [], "Cheeni", "Panchadara"),
    ("X004", "Salt", "173468", "vegan", "none", [], "Namak", "Uppu"),
    ("X005", "Honey", "169640", "vegetarian", "none", [], "Shahad", "Thene"),
    ("X006", "Tofu, firm", "172475", "vegan", "none", ["soy"], "Tofu", "Tofu"),
    ("X007", "Soya chunks (textured soy, defatted soy flour)", "174275", "vegan", "none", ["soy"], "Soya badi", "Soya chunks"),
    ("X008", "Oats, rolled", "173904", "vegan", "none", ["gluten"], "Jai", "Oats"),
    ("X009", "Coconut milk", "170172", "vegan", "none", [], "Nariyal doodh", "Kobbari paalu"),
    ("X010", "Fresh cream", "170859", "vegetarian", "dairy", ["dairy"], "Malai", "Meegada"),
    ("X011", "Sago (sabudana)", "169717", "vegan", "none", [], "Sabudana", "Saggubiyyam"),
    ("X012", "Cornflour", "169698", "vegan", "none", [], "Cornflour (corn starch)", "Corn flour"),
    ("X013", "Bread, whole wheat", "172688", "vegan", "none", ["gluten"], "Brown bread", "Brown bread"),
    ("X015", "Cheese, processed", "171290", "vegetarian", "dairy", ["dairy"], "Cheese", "Cheese"),
    ("X017", "Button mushrooms, UV- or sun-exposed", "169376", "vegan", "none", [], "Dhoop dikhaye mushroom", "Endabettina puttagodugulu"),
    ("X019", "Chickpeas, kabuli (white), dry", "173756", "vegan", "none", [], "Kabuli chana, safed chana", "Kabuli senagalu"),
    # Recommended foods that IFCT 2017 does not list (used to verify foods.json)
    ("X020", "Pumpkin seeds, dried", "170556", "vegan", "none", [], "Kaddu ke beej", "Gummadi ginjalu"),
    ("X021", "Wheat germ, crude", "168892", "vegan", "none", ["gluten"], "Gehun ke ankur", "Godhuma molaka"),
    ("X022", "Cod liver oil", "173577", "non_veg", "fish", ["seafood"], "Cod liver tel", "Cod liver nune"),
    ("X023", "Tempeh", "174272", "vegan", "none", ["soy"], "Tempeh", "Tempeh"),
    ("X024", "Soy milk, with added calcium and vitamins A and D", "172456", "vegan", "none", ["soy"], "Soya doodh", "Soya paalu"),
    ("X025", "Figs, dried", "174665", "vegan", "none", [], "Sukha anjeer", "Endu anjeer"),
]


def load(folder: Path):
    nutrient_by_id = {r["id"]: r["nutrient_nbr"] for r in csv.DictReader(open(folder / "nutrient.csv"))}
    descriptions = {r["fdc_id"]: r["description"] for r in csv.DictReader(open(folder / "food.csv"))}
    values = {}
    for r in csv.DictReader(open(folder / "food_nutrient.csv")):
        nbr = nutrient_by_id.get(r["nutrient_id"])
        if nbr:
            values.setdefault(r["fdc_id"], {})[nbr] = float(r["amount"])
    return descriptions, values


def micronutrients(fdc_id, values):
    v = values.get(fdc_id, {})
    b12 = v.get(NBR["vitamin_b12_ug"])
    d_ug = v.get(NBR["vitamin_d_ug"])
    return (round(b12, 2) if b12 is not None else None), (round(d_ug * 40, 1) if d_ug is not None else None)


def full_profile(fdc_id, values):
    v = values[fdc_id]
    get = lambda key: v.get(NBR[key], 0.0)
    carbs = max(0.0, get("carbs_total_g") - get("fibre_g"))
    profile = {"energy_kcal": int(round(get("energy_kcal"))), "protein_g": round(get("protein_g"), 2),
               "fat_g": round(get("fat_g"), 2), "carbs_g": round(carbs, 2), "fibre_g": round(get("fibre_g"), 2),
               "sugars_g": round(get("sugars_g"), 2), "saturated_fat_g": round(get("saturated_fat_g"), 3)}
    for key in ("cholesterol_mg", "sodium_mg", "potassium_mg", "calcium_mg", "magnesium_mg", "phosphorus_mg",
                "folate_ug", "vitamin_c_mg"):
        profile[key] = round(get(key), 1)
    profile["iron_mg"] = round(get("iron_mg"), 2)
    profile["zinc_mg"] = round(get("zinc_mg"), 2)
    b12, d_iu = micronutrients(fdc_id, values)
    profile["vitamin_d_iu"] = d_iu if d_iu is not None else 0.0
    profile["vitamin_b12_ug"] = b12 if b12 is not None else 0.0
    return profile


def apply(folder: Path, path: Path):
    descriptions, values = load(folder)
    data = json.loads(path.read_text(encoding="utf-8"))
    foods = [f for f in data["ingredients"] if not f["code"].startswith("X")]
    by_code = {f["code"]: f for f in foods}
    # Marine fish without a name match: median of the matched marine fish (approximate).
    matched_marine = [MARINE_BY_NAME[name][0] for name in MARINE_BY_NAME]
    b12s = [b for b in (micronutrients(i, values)[0] for i in matched_marine) if b is not None]
    ds = [d for d in (micronutrients(i, values)[1] for i in matched_marine) if d is not None]
    fish_default = (round(statistics.median(b12s), 2), round(statistics.median(ds), 1))

    for food in foods:
        p = food["per_100g"]
        match = MATCHES.get(food["code"])
        if food["group"] == "Marine Fish":
            match = MARINE_BY_NAME.get(food["name"])
        if match:
            fdc_id, quality = match
            assert fdc_id in descriptions, (food["code"], fdc_id)
            b12, d_iu = micronutrients(fdc_id, values)
            p["vitamin_b12_ug"] = b12 if b12 is not None else 0.0
            p["vitamin_d_iu"] = d_iu if d_iu is not None else 0.0
            food["b12_vitamin_d_source"] = {"usda_fdc_id": fdc_id, "usda_description": descriptions[fdc_id], "match": quality}
        elif food["animal_source"] != "none" or food["group"] == "Mushrooms":
            p["vitamin_b12_ug"], p["vitamin_d_iu"] = fish_default if food["group"] == "Marine Fish" else (None, None)
            food["b12_vitamin_d_source"] = {"match": "approximate",
                                            "basis": "median of matched marine fish" if food["group"] == "Marine Fish" else "no match; not used in plans for B12 or vitamin D"}
        else:
            p["vitamin_b12_ug"], p["vitamin_d_iu"] = 0.0, 0.0  # plant foods contain neither
    for code, name, fdc_id, diet, animal, allergens, hindi, telugu in EXTRA:
        assert fdc_id in descriptions, (code, fdc_id)
        foods.append({"code": code, "name": name, "scientific_name": "", "group": "Kitchen ingredients (USDA)",
                      "names": {"hi": hindi, "te": telugu}, "diet": diet, "animal_source": animal, "allergens": allergens,
                      "yield_factor": 1.0, "preparation": None, "usable_in_plans": True,
                      "per_100g": full_profile(fdc_id, values), "source": f"USDA FoodData Central SR Legacy {fdc_id}: {descriptions[fdc_id]}",
                      "notes": [], "b12_vitamin_d_source": {"usda_fdc_id": fdc_id, "usda_description": descriptions[fdc_id], "match": E}})
    for food in foods:  # plant foods count as having no B12 or vitamin D unless fortified (tempeh's trace B12 is mostly
        if food["code"] in ("X020", "X021", "X023", "X025"):  # inactive analogues)
            food["per_100g"]["vitamin_b12_ug"], food["per_100g"]["vitamin_d_iu"] = 0.0, 0.0
    # Derived items with a stated recipe.
    curd = next(f for f in foods if f["code"] == "X001")["per_100g"]
    foods.append({"code": "X016", "name": "Buttermilk (chaas), 1 part curd to 3 parts water", "scientific_name": "",
                  "group": "Kitchen ingredients (USDA)", "names": {"hi": "Chhaachh", "te": "Majjiga"}, "diet": "vegetarian",
                  "animal_source": "dairy", "allergens": ["dairy"], "yield_factor": 1.0, "preparation": None, "usable_in_plans": True,
                  "per_100g": {k: (round(v / 4, 3) if isinstance(v, float) else int(round(v / 4))) for k, v in curd.items()},
                  "source": "Derived: 25 g curd (USDA 171284) + 75 g water per 100 g", "notes": [],
                  "b12_vitamin_d_source": {"usda_fdc_id": "171284", "match": S}})
    milk = dict(by_code["L002"]["per_100g"])
    milk["vitamin_d_iu"] = 20.0  # FSSAI minimum: 5 micrograms per litre = 0.5 micrograms (20 IU) per 100 ml
    foods.append({"code": "X018", "name": "Milk, fortified (FSSAI +F), cow", "scientific_name": "", "group": "Kitchen ingredients (USDA)",
                  "names": {"hi": "Fortified doodh", "te": "Fortified paalu"}, "diet": "vegetarian", "animal_source": "dairy",
                  "allergens": ["dairy"], "yield_factor": 1.0, "preparation": None, "usable_in_plans": True, "per_100g": milk,
                  "source": "IFCT 2017 L002 cow milk, with vitamin D at the FSSAI fortification minimum (5 to 7.5 micrograms per litre)",
                  "notes": ["Fortification (Food Safety and Standards (Fortification of Foods) Regulations, 2018): vitamin D 5 to 7.5 micrograms per litre; the minimum is used."],
                  "b12_vitamin_d_source": {"usda_fdc_id": "172217", "match": E}})
    # Two Indian foods missing from IFCT 2017 and USDA: ICMR-NIN "Nutritive Value of Indian Foods" (NVIF) values per
    # 100 g. Only the nutrients NVIF reports are filled; the rest are unknown, so they are listed as uncertain.
    nvif = {"X026": ("Foxtail millet (kangni, korra)", {"energy_kcal": 331, "protein_g": 12.3, "fat_g": 4.3, "carbs_g": 60.9,
                                                       "fibre_g": 8.0, "calcium_mg": 31.0, "iron_mg": 2.8, "phosphorus_mg": 290.0},
                     "Kangni", "Korralu"),
            "X027": ("Makhana (fox nut, Euryale ferox), popped", {"energy_kcal": 347, "protein_g": 9.7, "fat_g": 0.1,
                                                                 "carbs_g": 76.9, "calcium_mg": 60.0, "iron_mg": 1.4,
                                                                 "phosphorus_mg": 90.0}, "Makhana", "Makhana")}
    for code, (name, values_100g, hindi, telugu) in nvif.items():
        profile = {key: 0.0 for key in foods[0]["per_100g"]}
        profile.update({k: float(v) for k, v in values_100g.items()})
        profile["vitamin_b12_ug"], profile["vitamin_d_iu"] = 0.0, 0.0
        foods.append({"code": code, "name": name, "scientific_name": "", "group": "Indian foods (NVIF)",
                      "names": {"hi": hindi, "te": telugu}, "diet": "vegan", "animal_source": "none", "allergens": [],
                      "yield_factor": 1.0, "preparation": None, "usable_in_plans": False, "per_100g": profile,
                      "source": "ICMR-NIN, Nutritive Value of Indian Foods (NVIF): not in IFCT 2017 or USDA SR Legacy",
                      "notes": ["Only the nutrients NVIF reports are filled."], "b12_vitamin_d_source": {"match": E},
                      "nvif_known": sorted(values_100g)})
    fish_groups = {"Marine Fish", "Fresh Water Fish and Shellfish", "Marine Shellfish", "Marine Mollusks"}
    for food in foods:
        source = food.get("b12_vitamin_d_source") or {}
        uncertain = []
        if source.get("match") == "approximate":
            uncertain = ["vitamin_b12_ug", "vitamin_d_iu"]
        elif food["group"] in fish_groups and source.get("match") != E:
            uncertain = ["vitamin_d_iu"]
        elif food["code"] == "X017":
            uncertain = ["vitamin_d_iu"]
        elif food.get("nvif_known"):
            uncertain = [k for k in food["per_100g"] if k not in food["nvif_known"] and k not in ("vitamin_b12_ug", "vitamin_d_iu")]
        food["uncertain"] = uncertain
    data["ingredients"] = foods
    data["sources"] = {"ifct": "Indian Food Composition Tables 2017, ICMR-NIN (machine-readable package, AGPL-3.0)",
                       "usda": "USDA FoodData Central, SR Legacy, April 2018 (public domain)"}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return foods, fish_default


if __name__ == "__main__":
    foods, fish_default = apply(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"{len(foods)} ingredients; approximate marine fish default B12 {fish_default[0]} ug, vitamin D {fish_default[1]} IU")
