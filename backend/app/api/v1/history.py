"""A signed-in person's own saved analyses, plus PDF export of the current result."""
import re
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.models.account_schemas import HistoryItem, HistoryMarker, HistoryPage
from app.models.database import get_db, utcnow
from app.models.entities import Report, User
from app.models.schemas import FullAnalysisResponse
from app.utils.pdf_generator import generate_plan_pdf

router = APIRouter()

NOT_FOUND = "Report not found."


def _own_report(db: Session, user: User, report_id: str) -> Report:
    # Someone else's report is indistinguishable from a missing one (404, never 403).
    report = db.query(Report).filter_by(id=report_id, owner_id=user.id).first()
    if report is None:
        raise HTTPException(404, NOT_FOUND)
    return report


def _summary(report: Report) -> HistoryItem:
    markers = [
        HistoryMarker(
            biomarker_key=m.get("biomarker_key", ""), display_name=m.get("display_name", ""),
            status=m.get("status", ""), value=m.get("value", 0), unit=m.get("unit", ""),
        )
        for m in report.analysis.get("marker_analyses", [])
    ]
    return HistoryItem(id=report.id, created_at=report.created_at, status_summary=report.status_summary,
                       marker_count=report.marker_count, requires_consult=report.requires_consult,
                       markers=markers)


@router.get("/history", response_model=HistoryPage)
def list_history(page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=50),
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Report).filter(Report.owner_id == user.id)
    total = query.count()
    reports = (query.order_by(Report.created_at.desc())
               .offset((page - 1) * page_size).limit(page_size).all())
    return HistoryPage(items=[_summary(r) for r in reports], total=total, page=page, page_size=page_size)


@router.get("/history/{report_id}", response_model=FullAnalysisResponse)
def get_report(report_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.plan.allergy import saved_report_conflicts
    analysis = _own_report(db, user, report_id).analysis
    return {**analysis, **saved_report_conflicts(analysis)}


class SavedPlan(BaseModel):
    style: str = Field(max_length=20)
    days: list = Field(min_length=1, max_length=7)
    shopping_list: list = Field(default_factory=list, max_length=300)


@router.put("/history/{report_id}/diet-plan", status_code=204)
def save_diet_plan(report_id: str, plan: SavedPlan, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """Keep the person's 7-day plan with the report it was built from."""
    report = _own_report(db, user, report_id)
    report.analysis = {**report.analysis, "diet_plan": {**plan.model_dump(), "saved_at": utcnow().isoformat()}}
    db.commit()


@router.delete("/history/{report_id}", status_code=204)
def delete_report(report_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(_own_report(db, user, report_id))
    db.commit()


@router.post("/export-plan-pdf")
def export_plan_pdf(analysis_data: FullAnalysisResponse, lang: str = "en"):
    """Generate and stream a branded A4 PDF of the analysis supplied in the request body (en, hi or te)."""
    analysis_data = analysis_data.model_dump(mode="json")

    try:
        pdf_bytes = generate_plan_pdf(analysis_data, lang)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate the PDF. Please retry with your current results."
        )

    # Caller-supplied IDs are labels only; this endpoint never reads stored reports.
    analysis_id = re.sub(r"[^A-Za-z0-9_-]", "", str(analysis_data.get("analysis_id", "nutrilens_plan")))
    filename = f"NutriLens_Plan_{analysis_id[:8]}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store",
        },
    )
