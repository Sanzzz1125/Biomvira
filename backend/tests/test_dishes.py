"""The dish catalog: ingredient names point to the right foods, nutrients are calculated correctly, and every dish
passes its checks."""
import re

import pytest

from app.plan import catalog as cat
from app.plan.dishes import Dish, dish, tempering
from app.plan.ingredient_names import INGREDIENTS, MIXES, TRACE, expand
from app.plan.nutrition import b12_class, calculate, ingredients, meat_type


# ingredient names -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(INGREDIENTS))
def test_ingredient_name_points_to_the_named_food(name):
    codes, check = INGREDIENTS[name]
    codes = [codes] if isinstance(codes, str) else list(codes)
    checks = [check] * len(codes) if isinstance(check, str) else list(check)
    assert len(checks) == len(codes)
    table = ingredients()
    for code, words in zip(codes, checks):
        assert code in table, f"{name}: {code} is not in ingredients.json"
        assert words.lower() in table[code]["name"].lower(), f"{name}: {code} is {table[code]['name']!r}"
        assert table[code]["usable_in_plans"]


def test_mixes_add_up_and_use_known_ingredients():
    for name, parts in MIXES.items():
        assert sum(share for _, share in parts) == pytest.approx(1.0), name
        for part, _ in parts:
            assert part in INGREDIENTS or part in TRACE, f"{name}: {part}"


def test_trace_items_are_not_also_real_ingredients():
    assert not TRACE & set(INGREDIENTS)
    assert expand("cinnamon", 1) == []
    assert expand("ginger-garlic paste", 4) == [("ginger", 2), ("garlic", 2)]


def test_cooking_oil_does_not_carry_a_nut_or_sesame_allergen():
    table = ingredients()
    assert table[INGREDIENTS["oil"][0]]["allergens"] == []
    assert table[INGREDIENTS["groundnut oil"][0]]["allergens"] == ["nuts"]
    assert table[INGREDIENTS["sesame oil"][0]]["allergens"] == ["sesame"]


# calculator ---------------------------------------------------------------------------------------------------------

def test_nutrients_scale_with_grams():
    rice = calculate([("A015", 55, "boiling")])["per_serving"]
    assert rice["energy_kcal"] == round(356 * 0.55)
    assert rice["protein_g"] == pytest.approx(7.94 * 0.55, abs=0.01)


def test_averaged_varieties_use_equal_parts():
    table = ingredients()
    expected = (table["D075"]["per_100g"]["vitamin_c_mg"] + table["D076"]["per_100g"]["vitamin_c_mg"]) / 2
    raw = calculate([(("D075", "D076"), 100, "none")])["per_serving"]
    assert raw["vitamin_c_mg"] == pytest.approx(expected, abs=0.01)


def test_ifct_retention_applies_only_to_heat_sensitive_vitamins():
    raw = calculate([("C033", 100, "none")])["per_serving"]
    boiled = calculate([("C033", 100, "boiling")])["per_serving"]
    assert boiled["vitamin_c_mg"] == pytest.approx(raw["vitamin_c_mg"] * 0.60, abs=0.01)
    assert boiled["folate_ug"] == pytest.approx(raw["folate_ug"] * 0.65, abs=0.01)
    for key in ("energy_kcal", "protein_g", "iron_mg", "calcium_mg", "potassium_mg"):
        assert boiled[key] == raw[key]


def test_usda_b12_retention_by_kind_of_food():
    def b12(code, method):
        return calculate([(code, 100, method)])["per_serving"]["vitamin_b12_ug"]

    assert b12("L002", "boiling") == pytest.approx(b12("L002", "none") * 0.80, abs=0.01)  # milk
    assert b12("M001", "frying") == pytest.approx(b12("M001", "none") * 0.85, abs=0.01)  # egg
    assert b12("N003", "boiling") == pytest.approx(b12("N003", "none") * 0.65, abs=0.01)  # chicken
    assert b12("O008", "boiling") == pytest.approx(b12("O008", "none") * 0.75, abs=0.01)  # goat liver
    assert b12("X001", "none") == ingredients()["X001"]["per_100g"]["vitamin_b12_ug"]  # curd added after cooking


@pytest.mark.parametrize("code,expected", [
    ("S010", "shellfish"), ("S009", "shellfish"), ("S007", "shellfish"), ("Q007", "shellfish"),
    ("R003", "shellfish"), ("S006", "fish"), ("P071", "fish"), ("M001", "egg"), ("N001", "chicken"),
    ("N007", "chicken"), ("N005", "chicken"), ("N012", "other_poultry"), ("O001", "mutton"), ("O021", "mutton"),
    ("O025", "beef"), ("O045", "beef"), ("O048", "pork"), ("O061", "other_meat"), ("L002", None), ("A015", None),
])
def test_meat_type(code, expected):
    assert meat_type(code, ingredients()[code]) == expected


@pytest.mark.parametrize("code,expected", [
    ("S010", "shellfish"), ("S006", "fish_lean"), ("P071", "fish_fatty"), ("N005", "organ"), ("O008", "organ"),
    ("N003", "poultry"), ("O003", "lamb"), ("O027", "beef"), ("O049", "pork"), ("L003", "cheese"),
    ("X001", "milk"), ("M001", "egg"), ("A015", None),
])
def test_b12_class(code, expected):
    assert b12_class(code, ingredients()[code]) == expected


def test_unknown_method_and_bad_grams_are_rejected():
    with pytest.raises(ValueError):
        calculate([("A015", 50, "baking")])
    with pytest.raises(ValueError):
        calculate([("A015", 0, "boiling")])


# the catalog --------------------------------------------------------------------------------------------------------

def test_every_dish_passes_its_checks():
    assert cat.problems() == {}
    assert len(cat.catalog()) == len(cat.all_dishes()) >= 120


def test_ids_are_simple_and_unique():
    ids = [d.id for d in cat.all_dishes()]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[a-z][a-z0-9_]*", i) for i in ids)


def test_every_region_and_meal_has_choices():
    dishes = cat.catalog().values()
    for region in ("telangana", "andhra", "tamil_nadu", "kerala", "karnataka", "punjab", "uttar_pradesh",
                   "jammu_kashmir", "maharashtra", "gujarat", "west_bengal", "bihar", "odisha"):
        regional = [d for d in dishes if region in d["regions"]]
        for role in ("staple", "breakfast", "dal", "curry", "liquid", "chutney", "rice_dish", "sweet"):
            assert any(d["role"] == role for d in regional), (region, role)
    for meal in cat.MEALS:
        assert sum(meal in d["meals"] for d in dishes) >= 10, meal


@pytest.mark.parametrize("dish_id,diet,meats", [
    ("phulka", "vegan", []), ("idli", "vegan", []), ("curd_rice", "vegetarian", []),
    ("mudda_pappu", "vegetarian", []), ("egg_curry", "eggetarian", ["egg"]),
    ("chicken_curry", "non_veg", ["chicken"]), ("mutton_biryani", "non_veg", ["mutton"]),
    ("chepala_pulusu", "non_veg", ["fish"]), ("royyala_iguru", "non_veg", ["shellfish"]),
    ("beef_ularthiyathu", "non_veg", ["beef"]), ("kerala_fish_curry", "non_veg", ["fish"]), ("appam", "vegan", []),
    ("avial", "vegetarian", []), ("egg_roast", "eggetarian", ["egg"]),
])
def test_diet_is_derived_from_ingredients(dish_id, diet, meats):
    d = cat.catalog()[dish_id]
    assert d["diet"] == diet
    assert d["meat_types"] == meats


@pytest.mark.parametrize("dish_id,allergens", [
    ("aloo_fry", ["mustard"]), ("steamed_rice", []), ("pulihora", ["mustard", "nuts"]),
    ("sarva_pindi", ["nuts", "sesame"]), ("semiya_payasam", ["dairy", "gluten", "nuts"]),
    ("curd_rice", ["dairy", "mustard"]), ("royyala_iguru", ["seafood"]), ("boiled_egg", ["eggs"]),
    ("bobbatlu", ["dairy", "gluten"]), ("kara_kuzhambu", ["mustard", "sesame"]), ("parotta", ["gluten"]),
    ("cabbage_thoran", ["mustard"]), ("rava_idli", ["dairy", "gluten", "mustard", "nuts"]), ("matta_rice", []),
])
def test_allergens_are_derived_from_ingredients(dish_id, allergens):
    assert cat.catalog()[dish_id]["allergens"] == allergens


def test_fish_vitamin_d_is_marked_uncertain():
    dishes = cat.catalog()
    assert "vitamin_d_iu" in dishes["chepala_pulusu"]["uncertain"]
    assert dishes["boiled_egg"]["uncertain"] == []


def test_treats_are_limited_in_a_week():
    for d in cat.catalog().values():
        if d["role"] == "sweet":
            assert d["max_per_week"] == 1, d["id"]
    for dish_id in ("medu_vada", "punugulu", "mirchi_bajji", "onion_pakoda", "sakinalu", "chicken_biryani"):
        assert cat.catalog()[dish_id]["max_per_week"] <= 2


def test_known_values_per_serving():
    dishes = cat.catalog()
    assert dishes["steamed_rice"]["per_serving"]["energy_kcal"] == 196
    assert 80 <= dishes["idli"]["per_serving"]["energy_kcal"] <= 116  # 2 idlis of 40-58 kcal each
    assert 25 <= dishes["chicken_biryani"]["per_serving"]["protein_g"] <= 32


# the checks catch mistakes ------------------------------------------------------------------------------------------

def _problems_of(test_dish: Dish) -> list:
    found = cat.recipe_problems(test_dish)
    return found or cat.value_problems(test_dish, cat.calculate(cat.lines_of(test_dish)))


def test_checks_catch_typing_mistakes():
    good = dish("t", "Test dal", "dal", "lunch", "all", "1 katori", 150, "boiling",
                [("toor dal", 30), ("salt", 1), *tempering(4)])
    assert _problems_of(good) == []
    salty = dish("t", "Test dal", "dal", "lunch", "all", "1 katori", 150, "boiling", [("toor dal", 30), ("salt", 30)])
    assert any("sodium" in p for p in _problems_of(salty))
    oily = dish("t", "Test dal", "dal", "lunch", "all", "1 katori", 150, "boiling", [("toor dal", 30), ("oil", 300)])
    assert any("kcal" in p for p in _problems_of(oily))
    assert any("unknown ingredient" in p for p in _problems_of(
        dish("t", "Test", "dal", "lunch", "all", "1 katori", 150, "boiling", [("toor dhal", 30)])))
    assert any("regions" in p for p in _problems_of(
        dish("t", "Test", "dal", "lunch", "mars", "1 katori", 150, "boiling", [("toor dal", 30)])))
    assert any("unknown method" in p for p in _problems_of(
        dish("t", "Test", "dal", "lunch", "all", "1 katori", 150, "boiling", [("toor dal", 30, "baking")])))


def test_every_dish_has_a_hindi_and_telugu_name():
    import re
    for d in cat.catalog().values():
        assert re.search("[\u0900-\u097F]", d["names"].get("hi", "")), d["id"]
        assert re.search("[\u0C00-\u0C7F]", d["names"].get("te", "")), d["id"]
