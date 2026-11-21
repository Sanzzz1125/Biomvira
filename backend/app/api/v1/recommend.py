import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_optional_user
from app.models.entities import Report, User
from app.models.schemas import (
    AnalysisRequest,
    FullAnalysisResponse,
    MarkerStatus
)
from app.engine.rule_engine import RuleEngine
from app.engine.recommender import RecommendationEngine
from app.engine.explanation_generator import generate_grounded_explanation
from app.models.database import get_db

router = APIRouter()
rule_engine = RuleEngine()
recommender = RecommendationEngine()

@router.post("/analyze-and-recommend", response_model=FullAnalysisResponse)
def analyze_and_recommend(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    from app.engine.unit_converter import convert_to_canonical
    try:
        for marker in request.biomarkers:
            convert_to_canonical(marker.biomarker_key, marker.value, marker.unit)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    if len({m.biomarker_key for m in request.biomarkers}) != len(request.biomarkers):
        raise HTTPException(422, "Resolve duplicate biomarkers before analysis.")
    analysis_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Evaluate each biomarker deterministically
    marker_analyses = []
    status_counts = {"low": 0, "borderline": 0, "normal": 0, "high": 0}

    for marker_input in request.biomarkers:
        res = rule_engine.evaluate_marker(marker_input, request.user_profile)
        marker_analyses.append(res)
        status_counts[res.status.value] += 1

    # 2. Generate personalized food recommendations
    recommendations = recommender.generate_recommendations(marker_analyses, request.user_profile)

    # 3. Generate grounded explanation
    explanation, requires_consult, consult_reasons = generate_grounded_explanation(
        marker_analyses, recommendations, user_profile=request.user_profile
    )

    response = FullAnalysisResponse(
        analysis_id=analysis_id,
        timestamp=timestamp,
        user_profile=request.user_profile,
        status_summary=status_counts,
        marker_analyses=marker_analyses,
        recommendations=recommendations,
        grounded_explanation=explanation,
        requires_physician_consult=requires_consult,
        consult_reasons=consult_reasons
    )

    # Guests get their result without anything being stored. Signed-in people get it saved
    # to their own private history.
    if user is not None:
        response.saved_to_history = True
        db.add(Report(
            id=analysis_id,
            owner_id=user.id,
            analysis=response.model_dump(mode="json"),
            status_summary=status_counts,
            marker_count=len(marker_analyses),
            requires_consult=bool(requires_consult),
        ))
        db.commit()
    return response


@router.post("/localize-analysis")
def localize_analysis(analysis: FullAnalysisResponse, lang: str = "en"):
    """The same results in Hindi or Telugu (results are stored in English)."""
    from app.i18n import LANGUAGES, localize_analysis as localize
    if lang not in LANGUAGES:
        raise HTTPException(422, "Unsupported language.")
    return localize(analysis.model_dump(mode="json"), lang)
