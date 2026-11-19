"""Write the dish catalog to a spreadsheet, one serving per row, for reference and for the project report.

Usage: python dish_review_sheet.py <output.xlsx>        (needs openpyxl: pip install openpyxl)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402

from app.plan.catalog import catalog  # noqa: E402

STATE_NAMES = {"all": "All of India", "telangana": "Telangana", "andhra": "Andhra Pradesh",
               "tamil_nadu": "Tamil Nadu", "kerala": "Kerala", "karnataka": "Karnataka", "punjab": "Punjab",
               "haryana": "Haryana", "delhi": "Delhi", "uttar_pradesh": "Uttar Pradesh", "uttarakhand": "Uttarakhand",
               "himachal_pradesh": "Himachal Pradesh", "jammu_kashmir": "Jammu and Kashmir", "ladakh": "Ladakh", "maharashtra": "Maharashtra", "gujarat": "Gujarat", "goa": "Goa", "rajasthan": "Rajasthan", "madhya_pradesh": "Madhya Pradesh", "chhattisgarh": "Chhattisgarh", "west_bengal": "West Bengal", "odisha": "Odisha", "bihar": "Bihar", "jharkhand": "Jharkhand", "assam": "Assam", "meghalaya": "Meghalaya", "manipur": "Manipur", "nagaland": "Nagaland", "mizoram": "Mizoram", "arunachal_pradesh": "Arunachal Pradesh", "sikkim": "Sikkim", "tripura": "Tripura"}
ROLE_LABELS = {
    "breakfast": "Breakfast", "staple": "Roti / rice", "rice_dish": "Rice dish", "dal": "Dal (pappu)",
    "curry": "Curry / fry", "liquid": "Sambar / rasam / pulusu", "chutney": "Chutney / podi", "side": "Side",
    "snack": "Snack", "drink": "Drink", "fruit": "Fruit", "sweet": "Sweet",
}
DIET_LABELS = {"vegan": "Vegan", "vegetarian": "Vegetarian", "eggetarian": "Egg", "non_veg": "Non-veg"}
NUTRIENTS = [
    ("Calories (kcal)", "energy_kcal", 0), ("Protein (g)", "protein_g", 1), ("Fat (g)", "fat_g", 1),
    ("Carbs (g)", "carbs_g", 1), ("Fibre (g)", "fibre_g", 1), ("Iron (mg)", "iron_mg", 1),
    ("Calcium (mg)", "calcium_mg", 0), ("Sodium (mg)", "sodium_mg", 0), ("Vitamin B12 (µg)", "vitamin_b12_ug", 2),
    ("Vitamin D (IU)", "vitamin_d_iu", 0), ("Vitamin C (mg)", "vitamin_c_mg", 1),
]
HOW_TO = [
    "NutriLens dish list",
    "",
    "Each row is ONE serving of one dish, the way it is usually cooked at home, with its nutrients.",
    "",
    "How the amounts are written",
    "  - Grams of raw ingredient, cleaned and peeled, before cooking. Water is not listed.",
    "  - 1 teaspoon of oil or ghee is about 5 g. 1 teaspoon of salt is about 5 g. 1 katori is about 150 ml.",
    "  - For deep-fried snacks, oil is the amount the food soaks up, not what is in the pan.",
    "  - 'Oil' means refined sunflower oil. Dishes made with groundnut, sesame or coconut oil say so.",
    "",
    "Where the numbers come from",
    "  - Indian Food Composition Tables 2017 (ICMR-National Institute of Nutrition).",
    "  - Vitamin B12 and vitamin D: USDA FoodData Central (Indian tables do not list B12).",
    "  - Cooking losses: IFCT 2017 retention factors (vitamin C, folate, vitamin D) and the USDA retention table (B12).",
    "  - Vitamin D of fish is an estimate and is marked in the notes.",
    "",
    "How the dishes were checked",
    "  - Energy per 100 g against the UK CoFID 2021 tables (South Asian home dishes): 20 of 26 matched dishes within",
    "    15%, all within 31% (batch 1); see backend/tests/test_dish_references.py for all.",
    "  - Amounts against standard Indian textbook recipes (Indian Nutrient Databank).",
    "  - A typical day in each state: salt 7-9 g (India's measured average is 8.0 g) and 26-33% of energy from fat.",
]


def grams_text(grams: float) -> str:
    if grams < 0.2:
        return "a pinch"
    return f"{grams:g} g"


def ingredients_text(lines: list) -> str:
    merged = {}
    for line in lines:
        merged[line["name"]] = merged.get(line["name"], 0) + line["grams"]
    return ", ".join(f"{name} {grams_text(round(grams, 2))}" for name, grams in merged.items())


def rows():
    dishes = list(catalog().values())
    role_order, state_order = list(ROLE_LABELS), list(STATE_NAMES)
    dishes.sort(key=lambda d: ([state_order.index(r) for r in d["regions"]], role_order.index(d["role"]), d["name"]))
    for d in dishes:
        yield ", ".join(STATE_NAMES[r] for r in d["regions"]), d


def write(path: Path) -> int:
    wb = Workbook()
    guide = wb.active
    guide.title = "About"
    for i, text in enumerate(HOW_TO, start=1):
        cell = guide.cell(row=i, column=1, value=text)
        if i == 1:
            cell.font = Font(bold=True, size=14)
        elif text and not text.startswith(" ") and i > 2 and HOW_TO[i - 2] == "":
            cell.font = Font(bold=True)
    guide.column_dimensions["A"].width = 120

    sheet = wb.create_sheet("Dishes")
    headers = (["#", "Region", "Dish", "Also called", "Type", "Meals", "One serving", "Ingredients (raw, one serving)"]
               + [label for label, _, _ in NUTRIENTS]
               + ["Diet", "Allergens", "At most per week", "Notes"])
    sheet.append(headers)
    count = 0
    for label, d in rows():
        count += 1
        values = d["per_serving"]
        notes = [d["note"]] if d["note"] else []
        if "vitamin_d_iu" in d["uncertain"]:
            notes.append("Vitamin D is an estimate.")
        sheet.append([count, label, d["name"], ", ".join(d["also_called"]), ROLE_LABELS[d["role"]],
                      ", ".join(d["meals"]), d["serving"], ingredients_text(d["ingredients"])]
                     + [round(values[key], places) if places else round(values[key]) for _, key, places in NUTRIENTS]
                     + [DIET_LABELS[d["diet"]], ", ".join(d["allergens"]) or "none",
                        d["max_per_week"] if d["max_per_week"] < 7 else "any day", " ".join(notes)])

    widths = [5, 30, 34, 28, 18, 22, 18, 70] + [11] * len(NUTRIENTS) + [11, 22, 11, 40]
    for i, width in enumerate(widths, start=1):
        sheet.column_dimensions[sheet.cell(row=1, column=i).column_letter].width = width
    header_fill = PatternFill("solid", fgColor="E8F3EF")
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "D2"
    sheet.auto_filter.ref = sheet.dimensions
    wb.active = 1
    wb.save(path)
    return count


if __name__ == "__main__":
    print(f"wrote {write(Path(sys.argv[1]))} dishes to {sys.argv[1]}")
