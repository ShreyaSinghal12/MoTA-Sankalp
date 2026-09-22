from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.applications import app_summary, create_application_row
from app.core.security import get_current_user
from app.db.database import get_db
from app.integrations import digilocker_mock, nsp_mock
from app.models.models import Application, User
from app.schemas.schemas import NSPImportRequest
from app.services import audit_service

router = APIRouter(prefix="/integrations", tags=["integrations (mock)"], dependencies=[Depends(get_current_user)])


@router.post("/nsp/import")
def nsp_import(body: NSPImportRequest = NSPImportRequest(), db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    records = nsp_mock.fetch_new_applications(body.count, body.scheme_id)
    created = []
    for r in records:
        nsp_id = r.pop("nsp_application_id")
        app = create_application_row(db, {**r, "applicant_id": nsp_id.replace("NSP-", "STU-")}, user.email, source="NSP_IMPORT")
        created.append({"nsp_application_id": nsp_id, **app_summary(app)})
    return {"gateway": "NSP_MOCK", "imported": len(created), "applications": created}


@router.post("/nsp/status-sync")
def nsp_status_sync(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    apps = db.query(Application).all()
    records = [{"application_number": a.application_number, "status": a.status} for a in apps]
    result = nsp_mock.push_status(records)
    audit_service.log(db, None, "NSP_STATUS_SYNC", user.email, {"records": len(records)})
    return result


@router.get("/digilocker/{applicant_id}")
def digilocker(applicant_id: str):
    return digilocker_mock.fetch_documents(applicant_id)
