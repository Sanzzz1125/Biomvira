"""Blood sugar, blood fats, kidney and liver tests: thresholds, conversions, food plans and row parsing."""
import pytest

from app.engine.recommender import RecommendationEngine
from app.engine.rule_engine import RuleEngine
from app.engine.unit_converter import convert_to_canonical
from app.models.schemas import DietType, MarkerInput, UserProfile
from app.parsers.regex_matcher import extract_biomarkers_with_regex as parse

MALE = UserProfile(age=45, gender="male")


def judge(key, value, unit, low=None, high=None, profile=MALE):
    return RuleEngine().evaluate_marker(
        MarkerInput(biomarker_key=key, value=value, unit=unit, reference_low=low, reference_high=high), profile)


@pytest.mark.parametrize("key,value,expected", [
    # HbA1c: normal <5.7, prediabetes 5.7-6.4, diabetes range >=6.5 (ADA)
    ("hba1c", 5.6, "normal"), ("hba1c", 5.7, "borderline"), ("hba1c", 6.4, "borderline"), ("hba1c", 6.5, "high"),
    # fasting glucose: 70-99 normal, 100-125 prediabetes, >=126 diabetes range, <70 low
    ("fasting_glucose", 99, "normal"), ("fasting_glucose", 100, "borderline"), ("fasting_glucose", 125, "borderline"),
    ("fasting_glucose", 126, "high"), ("fasting_glucose", 65, "low"),
    # two-hour / post-meal glucose: <140 normal, 140-199 prediabetes, >=200 diabetes range
    ("postprandial_glucose", 139, "normal"), ("postprandial_glucose", 140, "borderline"), ("postprandial_glucose", 200, "high"),
    # lipids (ATP III bands, the same ones printed on Indian lab reports)
    ("total_cholesterol", 199, "normal"), ("total_cholesterol", 200, "borderline"), ("total_cholesterol", 240, "high"),
    ("triglycerides", 149, "normal"), ("triglycerides", 150, "borderline"), ("triglycerides", 200, "high"),
    ("ldl_cholesterol", 99, "normal"), ("ldl_cholesterol", 100, "borderline"), ("ldl_cholesterol", 160, "high"),
    # HDL: higher is better
    ("hdl_cholesterol", 39, "low"), ("hdl_cholesterol", 45, "borderline"), ("hdl_cholesterol", 60, "normal"),
])
def test_standard_bands(key, value, expected):
    unit = "%" if key == "hba1c" else "mg/dL"
    assert judge(key, value, unit).status.value == expected


def test_printed_ranges_do_not_override_guideline_bands_for_sugar_and_lipids():
    # The lab prints 74-106 for fasting glucose and "4 - 6" for HbA1c, but the guideline bands decide the status.
    assert judge("fasting_glucose", 102, "mg/dL", 74, 106).status.value == "borderline"
    assert judge("hba1c", 6.3, "%", 4, 6).status.value == "borderline"
    # A multi-band lipid row can wrongly yield 200-239 as a "range"; it must be ignored.
    assert judge("total_cholesterol", 136, "mg/dL", 200, 239).status.value == "normal"


def test_doctor_warnings_at_diagnostic_and_dangerous_levels():
    assert judge("hba1c", 6.4, "%").clinical_warning is None
    assert "diagnose diabetes" in judge("hba1c", 6.5, "%").clinical_warning
    assert judge("fasting_glucose", 125, "mg/dL").clinical_warning is None
    assert "diagnose diabetes" in judge("fasting_glucose", 126, "mg/dL").clinical_warning
    assert "below 70" in judge("fasting_glucose", 60, "mg/dL").clinical_warning
    assert "pancreatitis" in judge("triglycerides", 500, "mg/dL").clinical_warning
    assert judge("triglycerides", 499, "mg/dL").clinical_warning is None
    assert judge("ldl_cholesterol", 189, "mg/dL").clinical_warning is None
    assert judge("ldl_cholesterol", 190, "mg/dL").clinical_warning


def test_kidney_and_liver_tests_use_the_printed_range_and_always_say_see_a_doctor():
    high = judge("creatinine", 1.35, "mg/dL", 0.7, 1.18)
    assert high.status.value == "high" and "review it with your doctor" in high.clinical_warning
    assert judge("sgot_ast", 14, "U/L", 0, 50).clinical_warning is None
    assert judge("total_protein", 6.4, "gm/dL", 6.6, 8.3).status.value == "low"
    # sex-specific fallback when the report prints no range
    assert judge("uric_acid", 6.5, "mg/dL", profile=UserProfile(age=40, gender="male")).status.value == "normal"
    assert judge("uric_acid", 6.5, "mg/dL", profile=UserProfile(age=40, gender="female")).status.value == "high"


@pytest.mark.parametrize("key,value,unit,expected", [
    ("hba1c", 53, "mmol/mol", 7.0), ("hba1c", 6.5, "%", 6.5), ("fasting_glucose", 5.0, "mmol/L", 90.08),
    ("total_cholesterol", 5.2, "mmol/L", 201.08), ("triglycerides", 1.7, "mmol/L", 150.57), ("creatinine", 88.4, "umol/L", 1.0),
    ("creatinine", 88.4, "µmol/L", 1.0), ("albumin", 40, "g/L", 4.0), ("sgot_ast", 30, "IU/L", 30.0),
])
def test_unit_conversions(key, value, unit, expected):
    assert convert_to_canonical(key, value, unit)[0] == pytest.approx(expected, abs=0.01)


def plans_for(values, **profile):
    profile = UserProfile(age=50, gender="male", **profile)
    engine = RuleEngine()
    markers = [engine.evaluate_marker(MarkerInput(biomarker_key=k, value=v, unit=u), profile) for k, v, u in values]
    return RecommendationEngine().generate_recommendations(markers, profile)


def test_high_sugar_gets_a_food_plan_but_kidney_values_do_not():
    plans = plans_for([("hba1c", 7.0, "%"), ("creatinine", 2.0, "mg/dL")])
    assert [p.biomarker_display_name for p in plans] == ["HbA1c (Glycated Haemoglobin)"]
    assert plans[0].recommended_foods and plans[0].absorption_dos and plans[0].absorption_donts
    assert any("medicine" in d for d in plans[0].absorption_donts)  # never tell people to change medicines on their own


def test_sugar_tests_sharing_advice_are_merged_into_one_plan():
    plans = plans_for([("hba1c", 6.3, "%"), ("fasting_glucose", 135, "mg/dL"), ("postprandial_glucose", 229, "mg/dL"),
                       ("ldl_cholesterol", 135, "mg/dL"), ("triglycerides", 260, "mg/dL")])
    assert len(plans) == 2
    assert plans[0].biomarker_display_name == "HbA1c · Fasting Blood Glucose · Post-Meal Blood Glucose"
    assert plans[0].status.value == "high" and plans[1].biomarker_display_name == "LDL Cholesterol · Triglycerides"


@pytest.mark.parametrize("diet,allergens,banned", [
    ("vegan", ["nuts"], {"almonds_badam", "cashewnuts_kaju"}),
    ("veg", ["soy"], {"tofu_firm", "tempeh", "soybean_cooked"}),
    ("non_veg", ["seafood"], {"mackerel_bangda", "hilsa_fish_ilish"}),
    ("veg", [], {"mackerel_bangda", "hilsa_fish_ilish"}),
])
def test_diet_and_allergen_rules_hold_for_the_new_plans(diet, allergens, banned):
    values = [("hba1c", 6.3, "%"), ("ldl_cholesterol", 150, "mg/dL"), ("hdl_cholesterol", 45, "mg/dL")]
    for plan in plans_for(values, diet_type=DietType(diet), allergens=allergens):
        assert plan.recommended_foods
        assert not banned & {f.id for f in plan.recommended_foods}


def test_every_tagged_food_label_comes_from_its_own_tags():
    for plan in plans_for([("hba1c", 6.3, "%")]):
        for food in plan.recommended_foods:
            assert set(food.key_nutrient_yield.split(" · ")) <= {"Low GI", "High fibre"}


# ------------------------------------------------------------------------------------------------- reading rows
def test_glycated_hemoglobin_is_hba1c_not_hemoglobin():
    markers = parse("Glycosylated Hemoglobin (HbA1c)   6.3   %   4.0 - 6.0\nHemoglobin (Hb)   13.2   g/dL   13.8 - 17.2")
    assert {m.biomarker_key: (m.detected_value, m.detected_unit) for m in markers} == {"hba1c": (6.3, "%"), "hemoglobin": (13.2, "g/dL")}


def test_ratio_rows_never_become_hdl_or_ldl():
    text = "S.HDL\n(Method: X)\n45 mg/dL Desirable Level : >60 mg/dL\nT.Chol/HDL\n(Method: Calculated)\n3.0 Low Risk: 3.3-4.4\nLDL/HDL\n(Method: Calculated)\n1.4 Desirable Level: 0.5-3.0"
    markers = parse(text)
    assert [(m.biomarker_key, m.detected_value) for m in markers] == [("hdl_cholesterol", 45.0)]


def test_band_text_is_not_mistaken_for_the_result_or_the_range():
    marker = parse("S.Triglycerides\n(Method: GPO-POD)\n139 mg/dL Desirable Level : <150\nmg/dL\nBorderline : 150 - 199 mg/dL\nHigh : 200 - 499 mg/dL")[0]
    assert (marker.detected_value, marker.detected_unit) == (139.0, "mg/dL")
    assert marker.report_reference_range is None and not marker.warnings and marker.abnormal_flag is None


def test_upper_limit_text_is_a_reference_not_a_second_result():
    marker = parse("SGPT /ALT\n(Method: UV)\n22 U/L < 50 U/L")[0]
    assert (marker.biomarker_key, marker.detected_value, marker.detected_unit, marker.warnings) == ("sgpt_alt", 22.0, "U/L", [])


def test_percent_and_mmol_per_mol_units_are_recognised():
    assert parse("HbA1c   53   mmol/mol   20 - 42")[0].detected_unit == "mmol/mol"
    assert parse("HbA1c   6.3 %   4 - 6 %")[0].detected_unit == "%"
