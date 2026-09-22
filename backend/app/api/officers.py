from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.applications import get_app_or_404
from app.core.security import get_current_user, require_roles
from app.db.database import get_db
from app.integrations import pfms_mock
from app.models.models import Application, OfficerAction, Payment, Sanction, User
from app.schemas.schemas import ActionRequest, row_to_dict
from app.services import audit_service, sanction_service

router = APIRouter(tags=["officer workflow"], dependencies=[Depends(get_current_user)])
officer_only = require_roles("ADMIN", "SCRUTINY_OFFICER", "MINISTRY_NODAL_OFFICER")

FINAL = ("APPROVED", "REJECTED", "SANCTIONED", "PAID")
AI_DONE = ("SCRUTINY_COMPLETED", "AI_FLAGGED", "MANUAL_REVIEW")


def _act(db: Session, app: Application, user: User, action: str, reason: str, new_status: str) -> dict:
    if app.status in FINAL:
        raise HTTPException(409, f"Application already {app.status}")
    if action != "MANUAL_REVIEW" and app.status not in AI_DONE:
        raise HTTPException(409, "Run scrutiny before approving or rejecting")
    overrode = (action == "APPROVE" and app.ai_recommendation == "RECOMMEND_REJECT") or \
               (action == "REJECT" and app.ai_recommendation == "RECOMMEND_APPROVE")
    oa = OfficerAction(application_id=app.id, officer_id=user.id, officer_email=user.email, action=action,
                       reason=reason, ai_recommendation_at_decision=app.ai_recommendation, overrode_ai=overrode)
    db.add(oa)
    app.status = new_status
    audit_service.log(db, app.id, f"OFFICER_{action}", user.email,
                      {"reason": reason, "ai_recommendation": app.ai_recommendation, "overrode_ai": overrode}, commit=False)
    db.commit()
    db.refresh(oa)
    return {"application_id": app.id, "status": app.status, "action": row_to_dict(oa)}


@router.post("/applications/{app_id}/approve")
def approve(app_id: int, body: ActionRequest, db: Session = Depends(get_db), user: User = Depends(officer_only)):
    return _act(db, get_app_or_404(db, app_id), user, "APPROVE", body.reason, "APPROVED")


@router.post("/applications/{app_id}/reject")
def reject(app_id: int, body: ActionRequest, db: Session = Depends(get_db), user: User = Depends(officer_only)):
    return _act(db, get_app_or_404(db, app_id), user, "REJECT", body.reason, "REJECTED")


@router.post("/applications/{app_id}/manual-review")
def manual_review(app_id: int, body: ActionRequest, db: Session = Depends(get_db), user: User = Depends(officer_only)):
    return _act(db, get_app_or_404(db, app_id), user, "MANUAL_REVIEW", body.reason, "MANUAL_REVIEW")


@router.post("/applications/{app_id}/sanction", status_code=201)
def create_sanction(app_id: int, db: Session = Depends(get_db), user: User = Depends(officer_only)):
    app = get_app_or_404(db, app_id)
    existing = db.query(Sanction).filter(Sanction.application_id == app.id).first()
    if existing:
        return {**row_to_dict(existing), "pdf_url": f"/api/v1/sanctions/{existing.id}/pdf"}
    if app.status != "APPROVED":
        raise HTTPException(409, "Only APPROVED applications can be sanctioned")
    s = Sanction(application_id=app.id, sanction_number=sanction_service.sanction_number(app),
                 amount=sanction_service.compute_amount(app), sanction_date=datetime.now(timezone.utc),
                 officer_email=user.email, status="SANCTIONED")
    db.add(s)
    db.flush()
    s.pdf_path = sanction_service.generate_pdf(app, s, user.email)
    app.status = "SANCTIONED"
    audit_service.log(db, app.id, "SANCTION_GENERATED", user.email,
                      {"sanction_number": s.sanction_number, "amount": s.amount}, commit=False)
    db.commit()
    db.refresh(s)
    return {**row_to_dict(s), "pdf_url": f"/api/v1/sanctions/{s.id}/pdf"}


@router.get("/sanctions/{sanction_id}/pdf")
def sanction_pdf(sanction_id: int, db: Session = Depends(get_db)):
    s = db.get(Sanction, sanction_id)
    if not s or not s.pdf_path or not Path(s.pdf_path).exists():
        raise HTTPException(404, "Sanction PDF not found")
    return FileResponse(s.pdf_path, media_type="application/pdf", filename=Path(s.pdf_path).name)


@router.post("/sanctions/{sanction_id}/payment")
def pay(sanction_id: int, db: Session = Depends(get_db), user: User = Depends(officer_only)):
    s = db.get(Sanction, sanction_id)
    if not s:
        raise HTTPException(404, "Sanction not found")
    existing = db.query(Payment).filter(Payment.sanction_id == s.id).first()
    if existing:
        return row_to_dict(existing)
    app = db.get(Application, s.application_id)
    resp = pfms_mock.initiate_payment(s.sanction_number, s.amount, app.full_name, db.query(Payment).count())
    p = Payment(sanction_id=s.id, application_id=app.id, payment_reference=resp["payment_reference"],
                amount=s.amount, status=resp["status"], response=resp)
    db.add(p)
    s.status = "PAID"
    app.status = "PAID"
    audit_service.log(db, app.id, "PAYMENT_COMPLETED", "PFMS_MOCK",
                      {"payment_reference": p.payment_reference, "amount": p.amount, "initiated_by": user.email}, commit=False)
    db.commit()
    db.refresh(p)
    return row_to_dict(p)
