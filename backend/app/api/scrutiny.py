from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents import mota_twin
from app.api.applications import get_app_or_404
from app.core.security import get_current_user
from app.db.database import get_db
from app.ml import anomaly_service, fuzzy_service
from app.models.models import Discrepancy, Document, User
from app.services import scrutiny_service

router = APIRouter(tags=["scrutiny"], dependencies=[Depends(get_current_user)])


@router.post("/applications/{app_id}/scrutiny")
def run_scrutiny(app_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    app = get_app_or_404(db, app_id)
    if app.status in ("APPROVED", "REJECTED", "SANCTIONED", "PAID"):
        raise HTTPException(409, f"Cannot re-run scrutiny on an application in status {app.status}")
    return scrutiny_service.run_scrutiny(db, app, user.email)


@router.post("/applications/{app_id}/twin/resolve/{discrepancy_id}")
def twin_resolve(app_id: int, discrepancy_id: int, db: Session = Depends(get_db)):
    """Re-run MoTA-Twin on one discrepancy (e.g. after new evidence was uploaded)."""
    app = get_app_or_404(db, app_id)
    d = db.get(Discrepancy, discrepancy_id)
    if not d or d.application_id != app.id:
        raise HTTPException(404, "Discrepancy not found")
    docs = db.query(Document).filter(Document.application_id == app.id).all()
    return mota_twin.resolve(d.issue_type, app, d.details or {}, docs)


@router.get("/ml/fuzzy")
def fuzzy(a: str, b: str):
    return fuzzy_service.compare_names(a, b)


@router.get("/ml/anomaly")
def anomaly(annual_income: float, marks_percentage: float, age: int, claimed_fee: float):
    return anomaly_service.score({"annual_income": annual_income, "marks_percentage": marks_percentage,
                                  "age": age, "claimed_fee": claimed_fee})
