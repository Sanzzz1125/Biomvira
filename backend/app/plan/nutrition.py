"""Nutrient values of a dish, calculated from its raw ingredients.

Each dish lists its ingredients as edible raw weight in grams per serving (cleaned and peeled, before cooking). The
nutrients of a serving are the sum of each ingredient's IFCT/USDA value per 100 g, scaled to its weight, with
published cooking losses applied to the vitamins heat destroys:

- Vitamin C, folate and vitamin D: IFCT 2017 retention factors by cooking method (retentionfactors/index.csv).
- Vitamin B12: USDA Table of Nutrient Retention Factors, Release 6 (2007), by kind of food and method. The "with
  drippings" factors are used because the gravy of Indian curries is eaten.
- Protein, minerals and energy are not reduced. IFCT's factors for those assume the cooking water is thrown away,
  while dal, sambar, pulusu and curries are eaten with their water.

An ingredient line can carry its own method: "none" for what is added after cooking (curd in curd rice, lemon
juice, garnish), or a different method for one step (the tempering of a raw chutney is fried).

Diet type, allergens and meat types are derived from the ingredients, never typed by hand.
"""
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

METHODS = ("boiling", "steaming", "frying", "roasting", "none")
NUTRIENT_KEYS = ["energy_kcal", "protein_g", "fat_g", "carbs_g", "fibre_g", "sugars_g", "saturated_fat_g",
                 "cholesterol_mg", "sodium_mg", "potassium_mg", "calcium_mg", "iron_mg", "zinc_mg", "magnesium_mg",
                 "phosphorus_mg", "folate_ug", "vitamin_c_mg", "vitamin_d_iu", "vitamin_b12_ug"]

# IFCT 2017 retention factors (steaming, roasting, frying, boiling), the same for every food.
RETENTION = {
    "vitamin_c_mg": {"steaming": 0.90, "roasting": 0.50, "frying": 0.60, "boiling": 0.60},
    "folate_ug": {"steaming": 0.91, "roasting": 0.75, "frying": 0.65, "boiling": 0.65},
    "vitamin_d_iu": {"steaming": 1.00, "roasting": 0.95, "frying": 0.90, "boiling": 0.90},
}
# USDA retention factors for vitamin B12 (Release 6). Where USDA has no row for a method, the closest one is used:
# steaming as simmering, and for organ meats roasting as frying.
B12_RETENTION = {
    "poultry": {"boiling": 0.65, "frying": 0.65, "roasting": 0.65, "steaming": 0.65},
    "lamb": {"boiling": 0.75, "frying": 0.80, "roasting": 0.75, "steaming": 0.75},  # goat and sheep
    "beef": {"boiling": 0.75, "frying": 0.80, "roasting": 0.70, "steaming": 0.75},
    "pork": {"boiling": 0.75, "frying": 0.90, "roasting": 0.80, "steaming": 0.75},
    "organ": {"boiling": 0.75, "frying": 0.80, "roasting": 0.80, "steaming": 0.75},
    "fish_lean": {"boiling": 0.95, "frying": 0.90, "roasting": 0.90, "steaming": 0.95},  # under 5 g fat per 100 g
    "fish_fatty": {"boiling": 0.95, "frying": 0.75, "roasting": 0.75, "steaming": 0.95},
    "shellfish": {"boiling": 0.90, "frying": 0.85, "roasting": 0.95, "steaming": 0.90},
    "egg": {"boiling": 0.85, "frying": 0.85, "roasting": 0.80, "steaming": 0.80},
    "milk": {"boiling": 0.80, "frying": 0.80, "roasting": 0.80, "steaming": 0.80},  # milk heated about 10 minutes
    "cheese": {"boiling": 0.55, "frying": 0.55, "roasting": 0.55, "steaming": 0.55},  # paneer, cheese
}
DIET_RANK = {"vegan": 0, "vegetarian": 1, "eggetarian": 2, "non_veg": 3}
FISH_GROUPS = {"Marine Fish", "Fresh Water Fish and Shellfish", "Marine Shellfish", "Marine Mollusks"}
SHELLFISH_CODES = {"S007", "S008", "S009", "S010"}  # freshwater crab and prawns; groups Q and R are all shellfish
ORGAN_WORDS = ("brain", "tongue", "lungs", "heart", "liver", "tripe", "spleen", "kidneys", "tube", "testis",
               "stomach", "gizzard")
CHEESE_CODES = {"L003", "X015"}  # paneer, processed cheese


@lru_cache(maxsize=1)
def ingredients() -> dict:
    data = json.loads((DATA / "ingredients.json").read_text(encoding="utf-8"))
    return {item["code"]: item for item in data["ingredients"]}


def _is_shellfish(code: str, food: dict) -> bool:
    return food["group"] in ("Marine Shellfish", "Marine Mollusks") or code in SHELLFISH_CODES


def meat_type(code: str, food: dict) -> str | None:
    """The kind of animal food, so a non-vegetarian can leave out what they never eat."""
    group = food["group"]
    if group in FISH_GROUPS:
        return "shellfish" if _is_shellfish(code, food) else "fish"
    if group == "Egg and Egg Products":
        return "egg"
    if group == "Poultry":
        return "chicken" if int(code[1:]) <= 10 else "other_poultry"  # N001-N010 chicken and country hen
    if group == "Animal Meat":
        number = int(code[1:])
        if number <= 24:
            return "mutton"  # goat and sheep
        if number <= 47:
            return "beef"  # beef, calf, mithun
        if number <= 57:
            return "pork"
        return "other_meat"  # hare, rabbit
    return None


def b12_class(code: str, food: dict) -> str | None:
    """Which USDA B12 retention row applies to an ingredient (None: no B12 to lose)."""
    group, name = food["group"], food["name"].lower()
    if group in ("Poultry", "Animal Meat") and any(word in name for word in ORGAN_WORDS):
        return "organ"
    kind = meat_type(code, food)
    if kind in ("chicken", "other_poultry"):
        return "poultry"
    if kind in ("mutton", "other_meat"):
        return "lamb"
    if kind in ("beef", "pork", "egg", "shellfish"):
        return kind
    if kind == "fish":
        return "fish_fatty" if (food["per_100g"]["fat_g"] or 0) > 5 else "fish_lean"
    if food["animal_source"] == "dairy":
        return "cheese" if code in CHEESE_CODES else "milk"
    return None


def resolve(codes) -> list:
    """An ingredient is one food code, or several varieties averaged (for example all ripe tomatoes)."""
    table = ingredients()
    return [(c, table[c]) for c in ([codes] if isinstance(codes, str) else codes)]


def retention(key: str, method: str, code: str, food: dict) -> float:
    if method == "none":
        return 1.0
    if key == "vitamin_b12_ug":
        kind = b12_class(code, food)
        return B12_RETENTION[kind][method] if kind else 1.0
    return RETENTION.get(key, {}).get(method, 1.0)


def calculate(lines) -> dict:
    """lines: [(codes, grams, method)] -> per-serving nutrients, diet, allergens, meat types, uncertain nutrients."""
    totals = {k: 0.0 for k in NUTRIENT_KEYS}
    contribution = {k: {} for k in NUTRIENT_KEYS}
    diet, allergens, meats, uncertain_codes = "vegan", set(), set(), {}
    for codes, grams, method in lines:
        if method not in METHODS:
            raise ValueError(f"Unknown cooking method: {method}")
        if grams <= 0:
            raise ValueError(f"{codes}: grams must be positive")
        varieties = resolve(codes)
        share = grams / len(varieties)  # averaging varieties = equal parts of each
        for code, food in varieties:
            for key in NUTRIENT_KEYS:
                amount = (food["per_100g"].get(key) or 0.0) * share / 100 * retention(key, method, code, food)
                totals[key] += amount
                contribution[key][code] = contribution[key].get(code, 0.0) + amount
            if DIET_RANK[food["diet"]] > DIET_RANK[diet]:
                diet = food["diet"]
            allergens.update(food["allergens"])
            kind = meat_type(code, food)
            if kind:
                meats.add(kind)
            uncertain_codes[code] = food.get("uncertain", [])
    # A nutrient is uncertain for the dish when uncertain ingredients supply more than a tenth of it.
    uncertain = set()
    for key in NUTRIENT_KEYS:
        if totals[key] > 0:
            share = sum(v for code, v in contribution[key].items() if key in uncertain_codes.get(code, []))
            if share / totals[key] > 0.1:
                uncertain.add(key)
    rounded = {k: (round(v) if k == "energy_kcal" else round(v, 2)) for k, v in totals.items()}
    return {"per_serving": rounded, "diet": diet, "allergens": sorted(allergens), "meat_types": sorted(meats),
            "uncertain": sorted(uncertain)}
