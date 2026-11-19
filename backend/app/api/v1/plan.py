"""Diet plans: three one-day options, a 7-day plan, swapping a dish, and a shopping list."""
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.plan import engine
from app.utils.diet_plan_pdf import generate_diet_plan_pdf

router = APIRouter()

Activity = Literal["none", "walking", "cycling", "running"]
Style = Literal["familiar", "nutritious", "regional"]
Slot = Literal["breakfast", "lunch", "snack", "dinner"]
GLUCOSE_MARKERS = {"hba1c", "fasting_glucose", "postprandial_glucose"}
LIPID_MARKERS = {"total_cholesterol", "triglycerides", "ldl_cholesterol"}


class FlaggedMarker(BaseModel):
    biomarker_key: str
    status: Literal["low", "borderline", "normal", "high"]
    target_nutrient_key: Optional[str] = None


class PlanProfile(BaseModel):
    age: int = Field(ge=18, le=100)
    gender: Literal["male", "female"]
    height_cm: float = Field(ge=120, le=220)
    weight_kg: float = Field(ge=30, le=200)
    activity: Activity = "none"
    diet_type: Literal["veg", "vegan", "eggetarian", "non_veg"] = "veg"
    meats: List[str] = Field(default_factory=list, max_length=8)
    allergens: List[str] = Field(default_factory=list, max_length=12)
    custom_allergies: List[str] = Field(default_factory=list, max_length=20)
    region: str = Field(default="", max_length=40)
    existing_diet: str = Field(default="", max_length=4000)


class PlanRequest(BaseModel):
    profile: PlanProfile
    markers: List[FlaggedMarker] = Field(default_factory=list, max_length=100)
    picked_foods: List[str] = Field(default_factory=list, max_length=30)
    style: Style = "familiar"


class SwapRequest(PlanRequest):
    day: dict
    slot: Slot
    dish_id: str = Field(max_length=60)


def person_from(request: PlanRequest) -> engine.Person:
    p = request.profile
    low = tuple(sorted({m.target_nutrient_key for m in request.markers
                        if m.status in ("low", "borderline") and m.target_nutrient_key in engine.REPORT_KEYS}))
    conditions = []
    if any(m.biomarker_key in GLUCOSE_MARKERS and m.status in ("high", "borderline") for m in request.markers):
        conditions.append("diabetes")
    if any(m.biomarker_key in LIPID_MARKERS and m.status in ("high", "borderline") for m in request.markers):
        conditions.append("high_cholesterol")
    return engine.Person(age=p.age, sex=p.gender, height_cm=p.height_cm, weight_kg=p.weight_kg, activity=p.activity,
                         diet=p.diet_type, meats=tuple(p.meats), allergens=tuple(p.allergens),
                         avoid_words=tuple(w[:40] for w in p.custom_allergies), region=p.region,
                         low_nutrients=low, conditions=tuple(conditions), picked_foods=tuple(request.picked_foods),
                         usual_diet=p.existing_diet)


@router.post("/diet-plan/options")
def plan_options(request: PlanRequest):
    person = person_from(request)
    found = engine.options(person)
    if not found:
        raise HTTPException(422, "We could not build a plan with these choices. Try removing an exclusion.")
    return {"options": found, "targets": engine.targets(person)}


@router.post("/diet-plan/week")
def plan_week(request: PlanRequest):
    person = person_from(request)
    days = engine.week(person, request.style)
    if not days:
        raise HTTPException(422, "We could not build a weekly plan with these choices.")
    return {"days": days, "shopping_list": engine.shopping_list(days), "targets": engine.targets(person)}


@router.post("/diet-plan/swap")
def plan_swap(request: SwapRequest):
    person = person_from(request)
    try:
        day = engine.swap(person, request.day, request.slot, request.dish_id, request.style)
    except (KeyError, TypeError):
        raise HTTPException(400, "That plan could not be read.")
    if day is None:
        raise HTTPException(422, "No other dish fits this meal. Try swapping a different dish.")
    return {"day": day}


class PdfRequest(BaseModel):
    days: list = Field(min_length=1, max_length=7)
    shopping_list: list = Field(default_factory=list, max_length=300)


@router.post("/diet-plan/pdf")
def plan_pdf(request: PdfRequest, lang: str = "en"):
    try:
        pdf = generate_diet_plan_pdf(request.days, request.shopping_list, lang=lang)
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, "That plan could not be read.")
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="NutriLens_7_day_plan.pdf"'})
