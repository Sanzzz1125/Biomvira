import pytest
from app.models.schemas import UserProfile, MarkerAnalysisResult, MarkerStatus, DietType
from app.engine.recommender import RecommendationEngine

@pytest.fixture
def recommender():
    return RecommendationEngine()

def test_allergen_dairy_filtering(recommender):
    # A vegetarian with dairy allergy MUST NOT be recommended paneer, curd, or cow milk
    profile = UserProfile(age=28, gender="male", diet_type=DietType.VEG, allergens=["dairy"])
    eligible = recommender.filter_foods(profile)
    
    for food in eligible:
        assert "dairy" not in [a.lower() for a in food.get("allergens", [])]
        assert food["id"] not in ["paneer_cottage_cheese", "curd_yogurt", "cow_milk_whole"]

def test_vegan_diet_filtering(recommender):
    # Vegan must never get dairy or animal foods
    profile = UserProfile(age=25, gender="female", diet_type=DietType.VEGAN, allergens=[])
    eligible = recommender.filter_foods(profile)
    
    for food in eligible:
        assert "vegan" in food["diet_type"]
        assert "dairy" not in food.get("allergens", [])
        assert "eggs" not in food.get("allergens", [])

def test_recommendation_generation_for_low_iron(recommender):
    profile = UserProfile(age=30, gender="female", diet_type=DietType.VEG, allergens=[])
    low_ferritin = MarkerAnalysisResult(
        biomarker_key="ferritin",
        display_name="Serum Ferritin",
        value=8.0,
        unit="ng/mL",
        status=MarkerStatus.LOW,
        range_low=15.0,
        range_high=307.0,
        percentage_of_optimal=53.3,
        clinical_warning="Low ferritin",
        target_nutrient_key="iron_mg"
    )

    plans = recommender.generate_recommendations([low_ferritin], profile)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.target_biomarker == "ferritin"
    assert len(plan.recommended_foods) > 0
    # Must have absorption guidelines
    assert len(plan.absorption_dos) > 0
    assert any("Vitamin C" in do for do in plan.absorption_dos)

