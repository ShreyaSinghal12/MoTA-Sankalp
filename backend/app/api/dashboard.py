from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.models import Application, AuditLog, Payment, Sanction
from app.schemas.schemas import row_to_dict

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    by_status = dict(db.query(Application.status, func.count()).group_by(Application.status).all())
    by_scheme = dict(db.query(Application.scheme_id, func.count()).group_by(Application.scheme_id).all())
    by_risk = dict(db.query(Application.risk_level, func.count()).group_by(Application.risk_level).all())
    disbursed = db.query(func.coalesce(func.sum(Payment.amount), 0)).scalar()
    recent = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(8).all()
    return {
        "total_applications": sum(by_status.values()),
        "pending": by_status.get("RECEIVED", 0),
        "under_scrutiny": by_status.get("UNDER_SCRUTINY", 0) + by_status.get("SCRUTINY_COMPLETED", 0),
        "ai_flagged": by_status.get("AI_FLAGGED", 0),
        "manual_review": by_status.get("MANUAL_REVIEW", 0),
        "approved": by_status.get("APPROVED", 0),
        "rejected": by_status.get("REJECTED", 0),
        "sanctioned": db.query(Sanction).count(),
        "paid": db.query(Payment).count(),
        "amount_disbursed": float(disbursed or 0),
        "by_status": by_status,
        "by_scheme": by_scheme,
        "by_risk": by_risk,
        "recent_activity": [row_to_dict(r) for r in recent],
    }
