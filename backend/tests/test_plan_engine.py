"""Diet plan engine: targets, filters and the plans the solver builds."""
import pytest

from app.plan.engine import Person, eligible, options, shopping_list, swap, targets, week

PERSON = Person(age=24, sex="female", height_cm=160, weight_kg=57, activity="moderate", diet="veg",
                allergens=("nuts", "sesame"), avoid_words=("brinjal",), region="telangana",
                low_nutrients=("iron_mg", "vitamin_b12_mcg"), picked_foods=("ifct_c022_gongura",))


def _dishes(day):
    return [i["dish_id"] for items in day["meals"].values() for i in items]


def test_targets_follow_the_equations():
    t = targets(PERSON)
    assert t["energy_kcal"] == round((14.7 * 57 + 496) * 1.70)  # FAO/WHO/UNU BMR x PAL for 4-5 workouts a week
    assert t["protein_g"] == round(0.83 * 57, 1)
    assert t["rda"]["iron_mg"] == 29 and t["low"] == ["iron_mg", "vitamin_b12_ug"]
    with pytest.raises(ValueError):
        targets(Person(age=15, sex="male", height_cm=160, weight_kg=50))


@pytest.mark.parametrize("activity,pal", [
    ("sedentary", 1.53), ("light", 1.60), ("moderate", 1.70), ("active", 1.80), ("very_active", 2.00),
    ("extra_active", 2.30),
    # values saved before the six levels: the nearest level
    ("none", 1.53), ("walking", 1.60), ("cycling", 1.80), ("running", 2.00), ("unknown", 1.53), (None, 1.53)])
def test_activity_levels(activity, pal):
    person = Person(age=24, sex="female", height_cm=160, weight_kg=50, activity=activity)  # BMI 19.5: no adjustment
    assert targets(person)["energy_kcal"] == round((14.7 * 50 + 496) * pal)


def test_filters_respect_diet_allergies_and_dislikes():
    for d in eligible(PERSON):
        assert d["diet"] in ("vegan", "vegetarian")
        assert not {"nuts", "sesame"} & set(d["allergens"])
        assert "brinjal" not in d["name"].lower() and "vankaya" not in d["name"].lower()
    meat_eater = Person(age=30, sex="male", height_cm=175, weight_kg=70, diet="non_veg", meats=("chicken",))
    kinds = {k for d in eligible(meat_eater) for k in d["meat_types"]}
    assert kinds <= {"chicken"}


@pytest.fixture(scope="module")
def three():
    return options(PERSON)


def test_three_options_meet_the_needs(three):
    assert [o["style"] for o in three] == ["familiar", "nutritious", "regional"]
    t = targets(PERSON)
    for o in three:
        assert 0.95 * t["energy_kcal"] <= o["totals"]["energy_kcal"] <= 1.05 * t["energy_kcal"]
        assert o["rda_met"]["iron_mg"] and o["rda_met"]["vitamin_b12_ug"]
        assert all(o["meals"][s] for s in ("breakfast", "lunch", "snack", "dinner"))
        assert "gongura" in " ".join(_dishes(o))  # the picked food is used
        allowed = {d["id"] for d in eligible(PERSON)}
        assert set(_dishes(o)) <= allowed


def test_options_differ(three):
    a, b = set(_dishes(three[0])), set(_dishes(three[1]))
    assert len(a & b) < len(a)


def test_week_varies_and_respects_weekly_limits():
    days = week(PERSON)
    assert len(days) == 7
    counts = {}
    for day in days:
        for dish_id in _dishes(day):
            counts[dish_id] = counts.get(dish_id, 0) + 1
    from app.plan.catalog import catalog
    for dish_id, c in counts.items():
        assert c <= catalog()[dish_id]["max_per_week"] * 2  # a dish can be in two meals of one day
    items = shopping_list(days)
    assert items and all(i["buy_g"] >= i["edible_g"] for i in items)


def test_swap_changes_only_one_dish(three):
    day = three[0]
    old = day["meals"]["lunch"][-1]["dish_id"]
    new = swap(PERSON, day, "lunch", old)
    assert new is not None
    assert old not in [i["dish_id"] for i in new["meals"]["lunch"]]
    key = lambda items: sorted((i["dish_id"], i["servings"]) for i in items)
    assert key(new["meals"]["breakfast"]) == key(day["meals"]["breakfast"])
