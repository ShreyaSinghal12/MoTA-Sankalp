import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.ml import duplicate_service
from app.models.models import (AgentResolution, Application, AuditLog, Discrepancy, Document, OfficerAction, Payment,
                               RiskResult, RuleResult, Sanction, User)
from app.schemas.schemas import ApplicationCreate, ApplicationUpdate, document_to_dict, row_to_dict
from app.services import audit_service, document_service

router = APIRouter(tags=["applications"], dependencies=[Depends(get_current_user)])


def get_app_or_404(db: Session, app_id: int) -> Application:
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(404, f"Application {app_id} not found")
    return app


def next_application_number(db: Session, scheme_id: str) -> str:
    n = db.query(Application).count() + 1
    return f"{scheme_id}-2026-{n:05d}"


def create_application_row(db: Session, data: dict, actor: str, source: str = "PORTAL") -> Application:
    app = Application(**data)
    app.source = source
    app.applicant_id = app.applicant_id or f"STU-{uuid.uuid4().hex[:8].upper()}"
    app.application_number = next_application_number(db, app.scheme_id)
    app.status = "RECEIVED"
    db.add(app)
    db.flush()
    audit_service.log(db, app.id, "APPLICATION_CREATED", actor,
                      {"application_number": app.application_number, "source": source}, commit=False)
    db.commit()
    db.refresh(app)
    return app


def app_summary(a: Application) -> dict:
    d = row_to_dict(a)
    d["document_count"] = len(a.documents)
    return d


@router.get("/applications")
def list_applications(status: Optional[str] = None, scheme_id: Optional[str] = None, state: Optional[str] = None,
                      risk_level: Optional[str] = None, q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Application)
    if status:
        query = query.filter(Application.status == status.upper())
    if scheme_id:
        query = query.filter(Application.scheme_id == scheme_id.upper())
    if state:
        query = query.filter(Application.state == state)
    if risk_level:
        query = query.filter(Application.risk_level == risk_level.upper())
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Application.full_name.ilike(like), Application.application_number.ilike(like)))
    return [app_summary(a) for a in query.order_by(Application.id).all()]


@router.post("/applications", status_code=201)
def create_application(body: ApplicationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return app_summary(create_application_row(db, body.model_dump(), user.email))


@router.get("/applications/{app_id}")
def get_application(app_id: int, db: Session = Depends(get_db)):
    a = get_app_or_404(db, app_id)
    resolutions = {r.discrepancy_id: row_to_dict(r) for r in
                   db.query(AgentResolution).filter(AgentResolution.application_id == app_id).all()}
    discrepancies = []
    for d in db.query(Discrepancy).filter(Discrepancy.application_id == app_id).order_by(Discrepancy.id).all():
        item = row_to_dict(d)
        item["resolution"] = resolutions.get(d.id)
        discrepancies.append(item)
    sanction = db.query(Sanction).filter(Sanction.application_id == app_id).first()
    payment = db.query(Payment).filter(Payment.application_id == app_id).first()
    return {
        "application": app_summary(a),
        "documents": [document_to_dict(d) for d in a.documents],
        "rule_results": [row_to_dict(r) for r in db.query(RuleResult).filter(RuleResult.application_id == app_id).all()],
        "risk_results": [row_to_dict(r) for r in db.query(RiskResult).filter(RiskResult.application_id == app_id).all()],
        "discrepancies": discrepancies,
        "officer_actions": [row_to_dict(o) for o in db.query(OfficerAction).filter(OfficerAction.application_id == app_id)
                            .order_by(OfficerAction.id).all()],
        "sanction": {**row_to_dict(sanction), "pdf_url": f"/api/v1/sanctions/{sanction.id}/pdf"} if sanction else None,
        "payment": row_to_dict(payment) if payment else None,
    }


@router.patch("/applications/{app_id}")
def update_application(app_id: int, body: ApplicationUpdate, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    a = get_app_or_404(db, app_id)
    if a.status in ("SANCTIONED", "PAID"):
        raise HTTPException(409, "Sanctioned applications cannot be edited")
    changes = body.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(a, k, v)
    audit_service.log(db, a.id, "APPLICATION_UPDATED", user.email, {"changes": changes}, commit=False)
    db.commit()
    db.refresh(a)
    return app_summary(a)


@router.post("/applications/{app_id}/documents", status_code=201)
async def upload_document(app_id: int, doc_type: str = Form(...), file: UploadFile = File(...),
                          db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = get_app_or_404(db, app_id)
    meta = await document_service.save_upload(a.id, doc_type, file)
    doc = Document(application_id=a.id, **meta)
    if not meta["file_path"].lower().endswith(".pdf"):
        doc.phash = duplicate_service.compute_phash(meta["file_path"])
    db.add(doc)
    db.flush()
    audit_service.log(db, a.id, "DOCUMENT_UPLOADED", user.email,
                      {"document_id": doc.id, "doc_type": doc.doc_type, "filename": doc.filename}, commit=False)
    db.commit()
    db.refresh(doc)
    return document_to_dict(doc)


@router.get("/documents/{doc_id}/file")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc or not Path(doc.file_path).exists():
        raise HTTPException(404, "Document not found")
    return FileResponse(doc.file_path, media_type=doc.content_type, filename=doc.filename)


@router.get("/applications/{app_id}/audit")
def audit_timeline(app_id: int, db: Session = Depends(get_db)):
    get_app_or_404(db, app_id)
    logs = db.query(AuditLog).filter(AuditLog.application_id == app_id).order_by(AuditLog.id).all()
    return [row_to_dict(x) for x in logs]
