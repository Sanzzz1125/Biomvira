"""Allergies: groups, typed words in any language or spelling, food cards, plans, saved reports and the assistant."""
import json
from pathlib import Path

import pytest

from app.chat.engine import ranked_foods
from app.engine.recommender import FOODS_DATABASE, RecommendationEngine
from app.models.schemas import DietType, UserProfile
from app.plan import allergy
from app.plan.catalog import catalog
from app.plan.engine import Person, eligible, food_codes, food_facts, options, swap, week
from app.plan.nutrition import ingredients

GROUPS = ("dairy", "gluten", "nuts", "soy", "eggs", "seafood", "sesame", "mustard")


def person(**kw):
    base = dict(age=30, sex="female", height_cm=160, weight_kg=58, activity="light", diet="non_veg", region="telangana")
    return Person(**{**base, **kw})


def removed(word):
    allowed = {d["id"] for d in eligible(person(avoid_words=(word,)))}
    return {d for d in catalog() if d not in allowed}


@pytest.mark.parametrize("words", [
    ["peanut", "groundnut", "Peanuts", "penut", "मूंगफली", "పల్లీలు", "verusenaga"],
    ["brinjal", "eggplant", "aubergine", "baingan", "बैंगन", "వంకాయ"],
    ["okra", "ladies finger", "bhindi", "బెండకాయ"],
])
def test_spellings_and_languages_mean_the_same_food(words):
    first = removed(words[0])
    assert first
    for word in words[1:]:
        assert removed(word) == first, word


def test_typed_words_are_whole_words_not_fragments():
    assert removed("egg") == {d["id"] for d in catalog().values() if "eggs" in d["allergens"]}  # not eggplant dishes
    assert removed("pea") == removed("green peas") | removed("dry peas")  # not peanut, pigeon pea or chickpea
    assert removed("oil") != set(catalog())  # sanity: a word never removes everything by accident


def test_unknown_words_are_reported_not_ignored_silently():
    assert not allergy.resolve("xyzzy").known and not removed("xyzzy")
    kiwi = allergy.resolve("kiwi")
    assert kiwi.known and not removed("kiwi")  # understood; no dish contains it


@pytest.mark.parametrize("word,group", [("milk", "dairy"), ("दूध", "dairy"), ("wheat", "gluten"), ("fish", "seafood"),
                                        ("prawns", "seafood"), ("til", "sesame"), ("సోయా", "soy"), ("anda", "eggs")])
def test_group_words_leave_out_the_whole_group(word, group):
    gone = removed(word)
    assert {d["id"] for d in catalog().values() if group in d["allergens"]} <= gone


def test_food_cards_carry_every_allergen_of_their_ingredients():
    table = ingredients()
    for food in FOODS_DATABASE:
        codes = food_codes(food["id"])
        assert codes and codes <= set(table), food["id"]
        assert {a for c in codes for a in table[c]["allergens"]} <= set(food["allergens"]), food["id"]


@pytest.mark.parametrize("group", GROUPS)
def test_food_cards_respect_every_allergy_group(group):
    shown = RecommendationEngine().filter_foods(UserProfile(diet_type=DietType.NON_VEG, allergens=[group]))
    assert shown and not [f["id"] for f in shown if group in food_facts(f)[1]]


@pytest.mark.parametrize("word,never", [("peanut", "ifct_h012_groundnut"), ("milk", "paneer_cottage_cheese"),
                                        ("fish", "rohu_freshwater_fish"), ("til", "sesame_seeds_til"),
                                        ("sarson", "ifct_c026_mustard_greens"), ("rai", "ifct_h013_mustard_seeds")])
def test_food_cards_respect_typed_allergies(word, never):
    shown = RecommendationEngine().filter_foods(UserProfile(diet_type=DietType.NON_VEG, custom_allergies=[word]))
    assert never not in {f["id"] for f in shown}


def test_food_cards_respect_the_meats_a_person_eats():
    shown = RecommendationEngine().filter_foods(UserProfile(diet_type=DietType.NON_VEG, meats=["chicken"]))
    meats = set().union(*(food_facts(f)[2] for f in shown))
    assert "chicken" in meats and not meats - {"chicken"}


def test_plans_weeks_and_swaps_never_contain_a_typed_allergy():
    p = person(avoid_words=("peanut", "coconut", "brinjal"), allergens=("sesame",))
    banned = set(catalog()) - {d["id"] for d in eligible(p)}
    days = options(p) + week(p)
    for day in days:
        assert not {i["dish_id"] for items in day["meals"].values() for i in items} & banned
    day = days[0]
    slot, items = next((s, it) for s, it in day["meals"].items() if it)
    swapped = swap(p, day, slot, items[0]["dish_id"])
    assert not {i["dish_id"] for its in swapped["meals"].values() for i in its} & banned


def test_saved_profile_keeps_everything_the_plans_need():
    data = {"age": 30, "gender": "female", "diet_type": "non_veg", "allergens": ["nuts"], "custom_allergies": ["peanut"],
            "meats": ["chicken"], "height_cm": 160, "weight_kg": 58, "activity": "moderate", "region": "telangana",
            "existing_diet": "idli, dosa"}
    assert UserProfile(**data).model_dump(mode="json") == data


def test_analysis_returns_the_full_profile(api):
    profile = {"age": 30, "gender": "female", "diet_type": "veg", "allergens": [], "custom_allergies": ["peanut"],
               "meats": [], "height_cm": 160, "weight_kg": 58, "activity": "active", "region": "andhra",
               "existing_diet": ""}
    response = api().post("/api/v1/analyze-and-recommend", json={"user_profile": profile, "biomarkers": [
        {"biomarker_key": "ferritin", "value": 8, "unit": "ng/mL"}]})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user_profile"]["custom_allergies"] == ["peanut"] and body["user_profile"]["activity"] == "active"
    foods = {f["id"] for p in body["recommendations"] for f in p["recommended_foods"]}
    assert "ifct_h012_groundnut" not in foods


def test_allergy_check_endpoint(api):
    response = api().post("/api/v1/diet-plan/allergy-check", json={"words": ["eggplant", "milk", "xyzzy"]})
    assert response.status_code == 200
    eggplant, milk, unknown = response.json()["results"]
    assert eggplant["known"] and eggplant["dishes_removed"] == len(removed("brinjal"))
    assert milk["groups"] == ["dairy"] and milk["foods_removed"] > 0
    assert not unknown["known"] and unknown["dishes_removed"] == 0 and unknown["foods_removed"] == 0


def test_assistant_food_lists_respect_typed_allergies():
    foods = ranked_foods("protein_support", "veg", ["peanut"], limit=50)
    assert foods and "ifct_h012_groundnut" not in {f["id"] for f in foods}


def test_foods_json_is_still_valid():
    data = json.loads((Path(__file__).resolve().parents[1] / "app" / "data" / "foods.json").read_text())
    assert len(data["foods"]) == 187
