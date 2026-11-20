"""Build backend/app/data/ingredients.json: every food in the Indian Food Composition Tables 2017 (IFCT, ICMR-NIN).

Usage: python -I build_ingredients.py <ifct package folder> <output.json>

The machine-readable IFCT package stores energy in kJ, proximates (protein, fat, carbohydrate, fibre, sugars) in g per
100 g edible portion, and every mineral and vitamin in GRAMS per 100 g. This script converts them to the units people
use (kcal, mg, micrograms) and adds what the plan engine needs: regional names, diet type, allergen groups, and IFCT's
own yield factor. Values are per 100 g of the edible, raw food, exactly as IFCT measured them; nothing is estimated here.
Documented corrections:
- Energy: IFCT leaves energy at 0 for the 13 oils and ghee although their fat is listed as 100 g. Their energy is
  calculated with IFCT's own energy factors (protein and carbohydrate 17 kJ/g, fat 37 kJ/g, fibre 8 kJ/g) and marked.
  The same calculation replaces one energy value that is a data-entry error (ENERGY_ENTRY_ERRORS).
- Vitamin D: the package reports vitamin D2/D3 for cereals, pulses and nuts (for example 41 micrograms per 100 g in
  ragi), which contradicts established nutrition science. IFCT vitamin D is therefore not used; vitamin D and B12 come
  from USDA FoodData Central in a later step, and other plant foods count as 0. The IFCT figure is kept in a note.
"""
import csv
import json
import re
import sys
from pathlib import Path

KJ_PER_KCAL = 4.184
ENERGY_KJ_PER_G = {"protcnt": 17, "fatce": 37, "choavldf": 17, "fibtg": 8}  # IFCT 2017 energy factors
MICROGRAM_IU_VITAMIN_D = 40  # 1 microgram of vitamin D = 40 IU (used only for the note)

# (output key, IFCT column, factor from IFCT units, decimals)
NUTRIENTS = [
    ("energy_kcal", "enerc", 1 / KJ_PER_KCAL, 0),
    ("protein_g", "protcnt", 1, 2),
    ("fat_g", "fatce", 1, 2),
    ("carbs_g", "choavldf", 1, 2),
    ("fibre_g", "fibtg", 1, 2),
    ("sugars_g", "fsugar", 1, 2),
    ("saturated_fat_g", "fasat", 1, 3),
    ("cholesterol_mg", "cholc", 1000, 1),
    ("sodium_mg", "na", 1000, 1),
    ("potassium_mg", "k", 1000, 1),
    ("calcium_mg", "ca", 1000, 1),
    ("iron_mg", "fe", 1000, 2),
    ("zinc_mg", "zn", 1000, 2),
    ("magnesium_mg", "mg", 1000, 1),
    ("phosphorus_mg", "p", 1000, 1),
    ("folate_ug", "folsum", 1e6, 1),
    ("vitamin_c_mg", "vitc", 1000, 1),
]

LANGUAGE_CODES = {"H": "hi", "Tel": "te", "Tam": "ta", "Kan": "kn", "Mal": "ml", "Mar": "mr", "G": "gu", "B": "bn",
                  "P": "pa", "O": "or", "U": "ur", "A": "as", "E": "en"}

SEAFOOD_GROUPS = {"Marine Fish", "Fresh Water Fish and Shellfish", "Marine Shellfish", "Marine Mollusks"}
# Allergen groups by exact IFCT code. Refined oils are included on purpose: strict filtering is safer.
ALLERGEN_CODES = {
    "nuts": {"H001", "H005", "H012", "H017", "H018", "H021", "T005"},  # almond, cashew, groundnut, pine, pistachio, walnut, groundnut oil
    "sesame": {"H009", "H010", "H011", "T004"},  # gingelly (sesame) seeds and oil
    "mustard": {"H013", "T006", "C026"},  # seeds, oil, and the leaves (sarson ka saag): people avoiding mustard expect all three
    "dairy": {"L001", "L002", "L003", "L004", "T013"},  # milks, paneer, khoa, ghee
    "gluten": {"A004", "A018", "A019", "A020", "A021", "A022", "A023", "A024"},  # barley and all wheat products
    "soy": {"B024", "B025", "T011"},
}
EXCLUDED_FROM_PLANS = {"K001": "alcoholic drink (toddy)"}
# Energy values that are data-entry errors in the package; recalculated from the food's own macronutrients.
ENERGY_ENTRY_ERRORS = {
    "N001": "IFCT lists 1605 kJ, twice what its protein and fat give (about 800 kJ, like the thigh and wing); recalculated.",
}


def regional_names(lang: str) -> dict:
    """'A., Kash. Baajra; Tel. Sajjalu; Tam. Kambu.' -> {'as': 'Baajra', 'te': 'Sajjalu', 'ta': 'Kambu'}"""
    names = {}
    for segment in lang.split(";"):
        match = re.match(r"\s*((?:[A-Z][a-z]*\.,?\s*)+)(.+)", segment)
        if not match:
            continue
        name = match.group(2).strip().rstrip(".").strip()
        for abbr in re.findall(r"([A-Z][a-z]*)\.", match.group(1)):
            code = LANGUAGE_CODES.get(abbr)
            if code and name and code not in names:
                names[code] = name
    return names


def diet_of(row) -> str:
    tags = row["tags"].split()
    if "veg" in tags:
        animal_free = row["grup"] != "Milk and Milk Products" and row["code"] != "T013"
        return "vegan" if animal_free else "vegetarian"
    if "eggetarian" in tags:
        return "eggetarian"
    return "non_veg"


def animal_source(row) -> str:
    group = row["grup"]
    if group in SEAFOOD_GROUPS:
        return "fish"
    if group in ("Animal Meat", "Poultry"):
        return "meat"
    if group == "Egg and Egg Products":
        return "egg"
    if group == "Milk and Milk Products" or row["code"] == "T013":
        return "dairy"
    return "none"


def allergens_of(row) -> list:
    found = [name for name, codes in ALLERGEN_CODES.items() if row["code"] in codes]
    if row["grup"] == "Egg and Egg Products":
        found.append("eggs")
    if row["grup"] in SEAFOOD_GROUPS:
        found.append("seafood")
    return sorted(found)


def build(package: Path) -> list:
    yields = {r["code"]: r for r in csv.DictReader(open(package / "yieldfactors" / "index.csv", encoding="utf-8"))}
    foods = []
    for row in csv.DictReader(open(package / "compositions" / "index.csv", encoding="utf-8")):
        per100, notes = {}, []
        for key, column, factor, decimals in NUTRIENTS:
            value = float(row[column]) * factor
            per100[key] = int(round(value)) if decimals == 0 else round(value, decimals)
        kj = sum(float(row[col]) * kj_per_g for col, kj_per_g in ENERGY_KJ_PER_G.items())
        if float(row["enerc"]) == 0 and kj > 0:
            per100["energy_kcal"] = int(round(kj / KJ_PER_KCAL))
            notes.append("Energy not given in IFCT; calculated from its macronutrients with IFCT energy factors.")
        if row["code"] in ENERGY_ENTRY_ERRORS:
            per100["energy_kcal"] = int(round(kj / KJ_PER_KCAL))
            notes.append(ENERGY_ENTRY_ERRORS[row["code"]])
        d2, d3 = float(row["ergcal"]) * 1e6, float(row["chocal"]) * 1e6
        if d2 + d3 > 0:
            notes.append(f"IFCT reports vitamin D {round((d2 + d3) * MICROGRAM_IU_VITAMIN_D)} IU per 100 g; not used (see module notes).")
        per100["vitamin_d_iu"] = None  # filled from USDA FoodData Central, or 0 for plant foods, in the next step
        per100["vitamin_b12_ug"] = None
        y = yields.get(row["code"], {})
        foods.append({
            "code": row["code"],
            "name": row["name"],
            "scientific_name": row["scie"],
            "group": row["grup"],
            "names": regional_names(row["lang"]),
            "diet": diet_of(row),
            "animal_source": animal_source(row),
            "allergens": allergens_of(row),
            "yield_factor": round(float(y["yield"]), 4) if y.get("yield") else None,
            "preparation": y.get("preparation") or None,
            "usable_in_plans": row["code"] not in EXCLUDED_FROM_PLANS,
            "per_100g": per100,
            "source": "IFCT 2017, ICMR-National Institute of Nutrition",
            "notes": notes,
        })
    return foods


if __name__ == "__main__":
    foods = build(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps({"ingredients": foods}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(foods)} ingredients to {sys.argv[2]}")
