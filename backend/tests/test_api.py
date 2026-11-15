from app.api.v1.recommend import analyze_and_recommend
from app.models.schemas import AnalysisRequest, UserProfile, MarkerInput, DietType


def test_analyze_and_recommend_endpoint():
    req = AnalysisRequest(
        user_profile=UserProfile(
            age=28,
            gender="female",
            diet_type=DietType.VEG,
            allergens=[]
        ),
        biomarkers=[
            MarkerInput(
                biomarker_key="vitamin_d",
                value=15.0,
                unit="ng/mL",
                reference_low=30.0,
                reference_high=100.0
            ),
            MarkerInput(
                biomarker_key="ferritin",
                value=8.0,
                unit="ng/mL",
                reference_low=15.0,
                reference_high=307.0
            )
        ]
    )
    # A guest (no signed-in user) never needs the database.
    res = analyze_and_recommend(req, db=None, user=None)
    assert res.analysis_id is not None
    assert res.saved_to_history is False
    assert res.status_summary["low"] == 2
    assert len(res.marker_analyses) == 2
    assert len(res.recommendations) == 2
    # Verify iron-rich foods are recommended (specific foods vary as DB grows)
    iron_plan = next(p for p in res.recommendations if p.target_biomarker == "ferritin")
    assert len(iron_plan.recommended_foods) > 0, "No iron foods recommended"
    # Ensure no zero-iron food slipped through
    for food in iron_plan.recommended_foods:
        assert food.key_nutrient_yield != "0.0 MG", f"Zero-iron food: {food.name}"
    # Ensure absorption dos/don'ts are present
    assert len(iron_plan.absorption_dos) > 0
    assert len(iron_plan.absorption_donts) > 0
