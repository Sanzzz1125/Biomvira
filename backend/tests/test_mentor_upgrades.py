"""Changes from the mentor review (ported from the team's second deployment): lab ranges with guideline sources,
advice that respects allergies and diet, beef and pork removed, shortfalls shown, saved-report conflicts."""
import itertools
import re

import pytest

from app.engine.allergen_rules import sanitize_tip_text
from app.engine.explanation_generator import BIOMARKER_CLINICAL_PROFILES
from app.engine.recommender import ABSORPTION_RULES
from app.engine.rule_engine import RuleEngine
from app.i18n import table
from app.models.schemas import MarkerInput, UserProfile
from app.plan.allergy import saved_report_conflicts
from app.plan.catalog import catalog
from app.plan.engine import Person, eligible, options, shopping_list


def test_no_beef_or_pork_anywhere_in_the_plans():
    assert len(catalog()) == 276
    assert not [d["id"] for d in catalog().values() if {"beef", "pork"} & set(d["meat_types"])]


def test_nuts_allergy_also_leaves_out_peanuts():
    kept = {d["id"] for d in eligible(Person(age=30, sex="female", height_cm=160, weight_kg=58, allergens=("nuts",)))}
    assert not [i for i in kept if any(x["name"] in ("peanuts", "groundnut oil") for x in catalog()[i]["ingredients"])]


@pytest.mark.parametrize("value,status", [(5.2, "normal"), (5.9, "borderline"), (6.9, "high")])
def test_lab_range_is_kept_and_status_follows_the_guideline(value, status):
    r = RuleEngine().evaluate_marker(MarkerInput(biomarker_key="hba1c", value=value, unit="%", reference_low=4.0,
                                                 reference_high=5.6), UserProfile())
    assert r.status.value == status and (r.lab_range_low, r.lab_range_high) == (4.0, 5.6)
    assert "6.5%" in r.guideline_threshold and r.guideline_source


def test_guideline_text_has_hindi_and_telugu():
    from app.engine.rule_engine import BIOMARKERS_CONFIG
    for cfg in BIOMARKERS_CONFIG.values():
        text = (cfg.get("clinical_guideline") or {}).get("threshold")
        if text:
            assert text in table("hi") and text in table("te"), text


TIPS = {t for r in ABSORPTION_RULES.values() for k in ("dos", "donts") for t in r.get(k, [])} | \
       {p.get("repletion_strategy", "") for p in BIOMARKER_CLINICAL_PROFILES.values()}
COMBOS = [(a, d) for d in ("veg", "vegan", "eggetarian", "non_veg") for n in range(4)
          for a in itertools.combinations(["nuts", "dairy", "seafood", "sesame", "soy", "eggs"], n)]


@pytest.mark.parametrize("allergens,diet", COMBOS)
def test_advice_never_suggests_an_excluded_food(allergens, diet):
    for tip in TIPS:
        text = sanitize_tip_text(tip, list(allergens), diet).lower()
        if "nuts" in allergens:
            assert not any(w in text for w in ("almond", "walnut", "cashew", "peanut", " nuts")), text
        if "dairy" in allergens or diet == "vegan":
            assert not any(w in text for w in ("ghee", "whole milk", "paneer", "curd,")), text
        if "sesame" in allergens:
            assert "sesame" not in text and "(til)" not in text, text
        if "soy" in allergens:
            assert "soya" not in text, text
        if "eggs" in allergens:
            assert not re.search(r"\beggs?\b", text), text
        if "seafood" in allergens:
            assert not re.search(r"\b(fish|mackerel)\b", text) or "limit" in text, text


def test_every_reworded_tip_has_hindi_and_telugu():
    reworded = {sanitize_tip_text(t, list(a), d) for t in TIPS for a, d in COMBOS} - TIPS
    assert reworded and all(t in table("hi") and t in table("te") for t in reworded)


def test_shortfalls_only_for_low_nutrients_still_short():
    day = options(Person(age=30, sex="female", height_cm=160, weight_kg=58, low_nutrients=("vitamin_d_iu",)))[0]
    assert set(day["shortfalls"]) <= {"vitamin_d_iu"}
    for key, s in day["shortfalls"].items():
        assert s["actual"] < s["target"] == day["targets"]["rda"][key]


def test_shopping_list_endpoint_follows_the_days(api):
    days = options(Person(age=30, sex="female", height_cm=160, weight_kg=58))[:1]
    response = api().post("/api/v1/diet-plan/shopping-list", json={"days": days})
    assert response.status_code == 200 and response.json()["shopping_list"] == shopping_list(days)


def test_saved_report_conflicts():
    peanut_dish = next(d for d in catalog().values() if any(i["name"] == "peanuts" for i in d["ingredients"]))
    plan = {"days": [{"meals": {"lunch": [{"dish_id": peanut_dish["id"], "name": peanut_dish["name"]},
                                          {"dish_id": "beef_ularthiyathu", "name": "Kerala beef fry"}],
                                "dinner": [{"dish_id": "steamed_rice", "name": "Steamed rice"}]}}]}
    analysis = {"user_profile": {"diet_type": "non_veg", "allergens": [], "custom_allergies": ["groundnut"]},
                "recommendations": [{"recommended_foods": [{"id": "ifct_h012_groundnut", "name": "Groundnut / Peanut"},
                                                           {"id": "palak_spinach", "name": "Spinach"}]}],
                "diet_plan": plan}
    found = saved_report_conflicts(analysis)
    assert found["can_regenerate"]
    assert found["allergy_conflicts"] == ["Groundnut / Peanut", peanut_dish["name"], "Kerala beef fry"]
    clean = {"user_profile": {"diet_type": "veg"}, "recommendations": [], "diet_plan": None}
    assert saved_report_conflicts(clean) == {"allergy_conflicts": [], "can_regenerate": False}
