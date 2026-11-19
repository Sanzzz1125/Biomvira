"""The dish catalog: every recipe, checked, with its nutrients per serving.

A dish that fails a check stops the catalog from loading, so a wrong amount can never reach a diet plan. The checks
are deliberately wide: they catch typing mistakes (300 g of salt, oil in kilograms), not differences between homes.
"""
from functools import lru_cache

from app.plan.dish_names import NAMES
from app.plan.dishes import basics, north, south, telugu, west_east
from app.plan.ingredient_names import INGREDIENTS, MIXES, TRACE, expand
from app.plan.nutrition import METHODS, calculate

MEALS = ("breakfast", "lunch", "dinner", "snack")
REGIONS = ("all", "telangana", "andhra", "tamil_nadu", "kerala", "karnataka", "punjab", "haryana", "delhi",
           "uttar_pradesh", "uttarakhand", "himachal_pradesh", "jammu_kashmir", "ladakh", "maharashtra", "gujarat", "goa",
           "rajasthan", "madhya_pradesh", "chhattisgarh", "west_bengal", "odisha", "bihar", "jharkhand", "assam",
           "meghalaya", "manipur", "nagaland", "mizoram", "arunachal_pradesh", "sikkim", "tripura")
# role: (lowest kcal, highest kcal per serving, lowest kcal per cooked gram, highest kcal per cooked gram)
ROLES = {
    "staple": (60, 450, 0.8, 4.0),       # rice, roti, sankati
    "rice_dish": (150, 700, 0.5, 2.6),   # pulihora, curd rice, biryani, khichdi, kanji (a thin gruel)
    "breakfast": (100, 500, 0.8, 3.6),   # idli, dosa, upma
    "dal": (60, 320, 0.4, 2.0),
    "curry": (30, 400, 0.2, 3.0),        # vegetable, egg, meat and fish curries and fries
    "liquid": (15, 220, 0.1, 1.2),       # sambar, rasam, pulusu
    "chutney": (10, 220, 0.3, 6.0),      # pachadi, podi
    "side": (10, 250, 0.1, 3.0),         # curd, raita, salad, boiled egg
    "snack": (50, 450, 0.5, 5.5),
    "drink": (0, 250, 0.0, 1.3),
    "fruit": (20, 200, 0.1, 1.6),        # watermelon is 0.2 kcal per gram
    "sweet": (80, 500, 1.0, 6.0),        # mysore pak is about 5.3 kcal per gram
}
MAX_SODIUM_MG = 1500  # per serving; about 3.9 g of salt
SOURCES = (basics, telugu, south, north, west_east)


def lines_of(dish) -> list:
    """(codes, grams, method) for the calculator, with mixes split into their parts and trace items dropped."""
    lines = []
    for line in dish.ingredients:
        name, grams = line[0], line[1]
        method = line[2] if len(line) > 2 else dish.method
        for part, part_grams in expand(name, grams):
            lines.append((INGREDIENTS[part][0], part_grams, method))
    return lines


def recipe_problems(dish) -> list:
    """Checks that need no nutrient values."""
    problems = []
    if dish.role not in ROLES:
        problems.append(f"unknown role {dish.role!r}")
    if not dish.meals or set(dish.meals) - set(MEALS):
        problems.append(f"meals must be among {MEALS}: {dish.meals}")
    if not dish.regions or set(dish.regions) - set(REGIONS):
        problems.append(f"regions must be among {REGIONS}: {dish.regions}")
    if dish.method not in METHODS:
        problems.append(f"unknown method {dish.method!r}")
    if dish.serving_g <= 0:
        problems.append("serving_g must be positive")
    if not 1 <= dish.max_per_week <= 7:
        problems.append("max_per_week must be 1 to 7")
    if not dish.ingredients:
        problems.append("no ingredients")
    for line in dish.ingredients:
        if len(line) not in (2, 3):
            problems.append(f"bad ingredient line {line}")
            continue
        name, grams = line[0], line[1]
        if name not in INGREDIENTS and name not in MIXES and name not in TRACE:
            problems.append(f"unknown ingredient {name!r}")
        if not isinstance(grams, (int, float)) or grams <= 0:
            problems.append(f"{name}: grams must be a positive number")
        if len(line) == 3 and line[2] not in METHODS:
            problems.append(f"{name}: unknown method {line[2]!r}")
    return problems


def value_problems(dish, values) -> list:
    """Checks on the calculated nutrients of one serving."""
    low, high, low_density, high_density = ROLES[dish.role]
    kcal = values["per_serving"]["energy_kcal"]
    problems = []
    if not low <= kcal <= high:
        problems.append(f"{kcal} kcal is outside {low}-{high} for a {dish.role}")
    density = kcal / dish.serving_g
    if not low_density <= density <= high_density:
        problems.append(f"{density:.2f} kcal per gram is outside {low_density}-{high_density} for a {dish.role}")
    if values["per_serving"]["sodium_mg"] > MAX_SODIUM_MG:
        problems.append(f"sodium {values['per_serving']['sodium_mg']} mg is above {MAX_SODIUM_MG} mg")
    return problems


def all_dishes() -> list:
    return [d for source in SOURCES for d in source.DISHES]


def problems() -> dict:
    """{dish id: [problems]} for every dish with at least one problem, plus duplicate ids and names."""
    found, ids, names = {}, set(), set()
    for dish in all_dishes():
        issues = recipe_problems(dish)
        if dish.id in ids:
            issues.append("duplicate id")
        if dish.name.lower() in names:
            issues.append("duplicate name")
        ids.add(dish.id)
        names.add(dish.name.lower())
        if not issues:
            issues = value_problems(dish, calculate(lines_of(dish)))
        if issues:
            found[dish.id] = issues
    return found


@lru_cache(maxsize=1)
def catalog() -> dict:
    """{dish id: dish with nutrients}; raises if any dish fails a check."""
    found = problems()
    if found:
        raise ValueError("Dish catalog has problems: " + "; ".join(f"{k}: {v}" for k, v in found.items()))
    result = {}
    for dish in all_dishes():
        values = calculate(lines_of(dish))
        result[dish.id] = {
            "id": dish.id,
            "name": dish.name,
            "names": NAMES.get(dish.id, {}),
            "also_called": list(dish.also_called),
            "role": dish.role,
            "meals": list(dish.meals),
            "regions": list(dish.regions),
            "serving": dish.serving,
            "serving_g": dish.serving_g,
            "max_per_week": dish.max_per_week,
            "ingredients": [{"name": line[0], "grams": line[1]} for line in dish.ingredients],
            "note": dish.note,
            **values,
        }
    return result
