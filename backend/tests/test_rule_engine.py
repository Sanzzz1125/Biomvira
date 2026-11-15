import pytest
from app.models.schemas import MarkerInput, UserProfile, MarkerStatus, DietType
from app.engine.rule_engine import RuleEngine

@pytest.fixture
def engine():
    return RuleEngine()

@pytest.fixture
def standard_female_profile():
    return UserProfile(age=26, gender="female", diet_type=DietType.VEG, allergens=[])

def test_vitamin_d_low_evaluation(engine, standard_female_profile):
    marker = MarkerInput(
        biomarker_key="vitamin_d",
        value=14.5,
        unit="ng/mL",
        reference_low=30.0,
        reference_high=100.0
    )
    res = engine.evaluate_marker(marker, standard_female_profile)
    assert res.status == MarkerStatus.LOW
    assert res.value == 14.5
    assert res.range_low == 30.0
    assert res.percentage_of_optimal < 50.0

def test_vitamin_d_severe_warning(engine, standard_female_profile):
    marker = MarkerInput(
        biomarker_key="vitamin_d",
        value=7.8,
        unit="ng/mL"
    )
    res = engine.evaluate_marker(marker, standard_female_profile)
    assert res.status == MarkerStatus.LOW
    assert res.clinical_warning is not None
    assert "severely depleted" in res.clinical_warning

def test_ferritin_female_baseline_fallback(engine, standard_female_profile):
    # Missing report ranges, should use female standard baseline (low: ~11-15, high: ~307)
    marker = MarkerInput(
        biomarker_key="ferritin",
        value=45.0,
        unit="ng/mL"
    )
    res = engine.evaluate_marker(marker, standard_female_profile)
    assert res.status == MarkerStatus.NORMAL
    assert res.range_low > 0
    assert res.range_high >= 300.0

def test_unit_conversion_during_evaluation(engine, standard_female_profile):
    # Vit D 25 nmol/L is ~10 ng/mL -> should be classified as LOW
    marker = MarkerInput(
        biomarker_key="vitamin_d",
        value=25.0,
        unit="nmol/L",
        reference_low=75.0, # 75 nmol/L is 30 ng/mL
        reference_high=250.0
    )
    res = engine.evaluate_marker(marker, standard_female_profile)
    assert res.status == MarkerStatus.LOW
    assert res.unit == "ng/mL"
    assert res.value <= 11.0

