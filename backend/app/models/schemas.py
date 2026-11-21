from typing import Annotated, Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum

class DietType(str, Enum):
    VEG = "veg"
    VEGAN = "vegan"
    EGGETARIAN = "eggetarian"
    NON_VEG = "non_veg"

class MarkerStatus(str, Enum):
    LOW = "low"
    BORDERLINE = "borderline"
    NORMAL = "normal"
    HIGH = "high"

Activity = Literal["sedentary", "light", "moderate", "active", "very_active", "extra_active",
                   "none", "walking", "cycling", "running"]  # the last four: saved before November 2026


class UserProfile(BaseModel):
    """Everything the person told us. Saved with the report, so a reopened report rebuilds the same plans with the
    same typed allergies, meats, body measurements, activity and region."""
    age: int = Field(default=25, ge=1, le=120)
    gender: str = Field(default="female", description="male or female for sex-specific reference ranges")
    diet_type: DietType = Field(default=DietType.VEG)
    allergens: List[str] = Field(default_factory=list, max_length=12,
                                 description="e.g. ['dairy', 'nuts', 'gluten', 'soy', 'eggs', 'seafood']")
    custom_allergies: List[Annotated[str, Field(max_length=40)]] = Field(default_factory=list, max_length=20)
    meats: List[Annotated[str, Field(max_length=20)]] = Field(default_factory=list, max_length=8)
    height_cm: Optional[float] = Field(default=None, ge=30, le=272)
    weight_kg: Optional[float] = Field(default=None, ge=2, le=400)
    activity: Activity = "sedentary"
    region: str = Field(default="", max_length=40)
    existing_diet: str = Field(default="", max_length=4000)

class ReferenceRange(BaseModel):
    low: Optional[float] = None
    high: Optional[float] = None

class DetectedBiomarker(BaseModel):
    biomarker_key: str
    display_name: str
    detected_value: float
    detected_unit: str
    canonical_value: Optional[float]
    canonical_unit: str
    report_reference_range: Optional[ReferenceRange] = None
    extraction_method: str = "regex" # "regex" or "llm_fallback" or "manual"
    confidence: Optional[float] = None
    verification_status: str = "needs_review"
    qualifier: Optional[str] = None
    source_page: Optional[int] = None
    source_text: Optional[str] = None
    abnormal_flag: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

class ExtractionResponse(BaseModel):
    session_id: str
    sanitized_preview: str
    extracted_biomarkers: List[DetectedBiomarker]
    warnings: List[str] = Field(default_factory=list)
    unmatched_text_lines: List[str] = Field(default_factory=list)

class MarkerInput(BaseModel):
    biomarker_key: str
    value: float
    unit: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None

class AnalysisRequest(BaseModel):
    user_profile: UserProfile
    biomarkers: List[MarkerInput]

class MarkerAnalysisResult(BaseModel):
    biomarker_key: str
    display_name: str
    value: float
    unit: str
    status: MarkerStatus
    range_low: float
    range_high: float
    percentage_of_optimal: float
    clinical_warning: Optional[str] = None
    target_nutrient_key: str
    lab_range_low: Optional[float] = None
    lab_range_high: Optional[float] = None
    guideline_threshold: Optional[str] = None
    guideline_source: Optional[str] = None

class FoodRecommendation(BaseModel):
    id: str
    name: str
    hindi_name: Optional[str] = None
    category: str
    serving_size: str
    key_nutrient_yield: str
    synergies: List[str] = Field(default_factory=list)
    preparation_tip: Optional[str] = None

class NutrientRecommendationPlan(BaseModel):
    target_biomarker: str
    biomarker_display_name: str
    status: MarkerStatus
    recommended_foods: List[FoodRecommendation]
    absorption_dos: List[str]
    absorption_donts: List[str]
    purpose: str = "improve"  # "improve" for out-of-range results, "maintain" for healthy ones

class FullAnalysisResponse(BaseModel):
    analysis_id: str
    timestamp: str
    user_profile: UserProfile
    status_summary: Dict[str, int]
    marker_analyses: List[MarkerAnalysisResult]
    recommendations: List[NutrientRecommendationPlan]
    grounded_explanation: str
    requires_physician_consult: bool
    consult_reasons: List[str]
    saved_to_history: bool = False
    diet_plan: Optional[Dict[str, Any]] = None
    allergy_conflicts: List[str] = Field(default_factory=list)
    can_regenerate: bool = False

