"""Diet plan API: request validation and responses."""
PROFILE = {"age": 24, "gender": "female", "height_cm": 160, "weight_kg": 57, "activity": "walking",
           "diet_type": "veg", "allergens": ["nuts"], "custom_allergies": ["brinjal"], "region": "telangana"}
MARKERS = [{"biomarker_key": "ferritin", "status": "low", "target_nutrient_key": "iron_mg"},
           {"biomarker_key": "hba1c", "status": "high", "target_nutrient_key": "glycemic_support"}]


BASE = "/api/v1"


def test_options_week_and_swap(api):
    api = api()
    base = BASE
    body = {"profile": PROFILE, "markers": MARKERS, "picked_foods": ["ifct_c022_gongura"]}
    r = api.post(f"{base}/diet-plan/options", json=body)
    assert r.status_code == 200, r.text
    options = r.json()["options"]
    assert len(options) == 3
    for o in options:  # raised HbA1c: no sweets
        assert all(i["role"] != "sweet" for items in o["meals"].values() for i in items)
    day = options[0]
    dish = day["meals"]["dinner"][-1]["dish_id"]
    r = api.post(f"{base}/diet-plan/swap", json={**body, "day": day, "slot": "dinner", "dish_id": dish})
    assert r.status_code == 200, r.text
    r = api.post(f"{base}/diet-plan/week", json={**body, "style": "regional"})
    assert r.status_code == 200 and len(r.json()["days"]) == 7 and r.json()["shopping_list"]
    week = r.json()
    r = api.post(f"{base}/diet-plan/pdf", json={"days": week["days"], "shopping_list": week["shopping_list"]})
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


def test_rejects_bad_profiles(api):
    api = api()
    base = BASE
    r = api.post(f"{base}/diet-plan/options", json={"profile": {**PROFILE, "age": 12}})
    assert r.status_code == 422


def test_plan_is_saved_with_the_owners_report_only(signed_in):
    from tests.test_auth_roles import ANALYSIS
    owner, other = signed_in("planowner@example.com"), signed_in("planother@example.com")
    report_id = owner.post("/api/v1/analyze-and-recommend", json=ANALYSIS).json()["analysis_id"]
    plan = {"style": "familiar", "days": [{"meals": {}, "totals": {}}], "shopping_list": []}
    assert other.client.put(f"/api/v1/history/{report_id}/diet-plan", json=plan,
                            headers=other._headers({})).status_code == 404
    assert owner.client.put(f"/api/v1/history/{report_id}/diet-plan", json=plan,
                            headers=owner._headers({})).status_code == 204
    saved = owner.get(f"/api/v1/history/{report_id}").json()["diet_plan"]
    assert saved["style"] == "familiar" and saved["saved_at"]
