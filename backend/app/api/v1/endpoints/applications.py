from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.application import Application, StatusEnum
from app.models.applicant import Applicant
from app.schemas.application import ApplicationCreateSchema, ApplicationSchema, ApplicationDetailSchema
from app.services.document_service import DocumentService
from app.services.rule_engine import rule_engine
from datetime import datetime

router = APIRouter(tags=["applications"])

@router.post("/applications", response_model=ApplicationSchema)
async def create_application(
    app_create: ApplicationCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_app = db.query(Application).filter(
        Application.applicant_id == app_create.applicant_id,
        Application.scheme_id == app_create.scheme_id
    ).first()
    
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already exists for this applicant and scheme"
        )
    
    new_application = Application(
        scheme_id=app_create.scheme_id,
        applicant_id=app_create.applicant_id,
        status=StatusEnum.RECEIVED,
        category=app_create.category,
        age=app_create.age,
        annual_income=app_create.annual_income,
        qualification=app_create.qualification,
        gender=app_create.gender
    )
    
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    
    return new_application

@router.get("/applications/{application_id}", response_model=ApplicationDetailSchema)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    documents = DocumentService.get_application_documents(application_id)
    
    return {
        "id": application.id,
        "scheme_id": application.scheme_id,
        "applicant_id": application.applicant_id,
        "status": application.status,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
        "category": application.category,
        "age": application.age,
        "annual_income": application.annual_income,
        "qualification": application.qualification,
        "gender": application.gender,
        "documents": documents,
        "evaluation_result": None
    }

@router.post("/applications/{application_id}/documents")
async def upload_document(
    application_id: int,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    success, message, file_path = await DocumentService.save_document(
        file=file,
        doc_type=doc_type,
        applicant_id=application.applicant_id,
        application_id=application_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "status": "success",
        "message": message,
        "file_path": file_path,
        "document_type": doc_type
    }

@router.post("/applications/{application_id}/evaluate")
async def evaluate_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    applicant_data = {
        "id": application.applicant_id,
        "category": application.category,
        "age": application.age,
        "annual_income": application.annual_income,
        "qualification": application.qualification,
        "documents": [doc.get("doc_type", "UNKNOWN") for doc in DocumentService.get_application_documents(application_id)],
        "duplicate_application_detected": False,
        "document_forgery_detected": False
    }
    
    try:
        evaluation = rule_engine.evaluate_eligibility(application.scheme_id, applicant_data)
        
        application.status = StatusEnum.UNDER_SCRUTINY
        db.commit()
        
        return {
            "application_id": application_id,
            "scheme_id": application.scheme_id,
            "evaluation": {
                "overall_status": evaluation.overall_status,
                "overall_score": evaluation.overall_score,
                "rules_passed": evaluation.rules_passed,
                "rules_total": evaluation.rules_total,
                "rule_results": [
                    {
                        "rule_id": r.rule_id,
                        "rule_name": r.rule_name,
                        "passed": r.passed,
                        "weight": r.weight,
                        "description": r.description,
                        "reason": r.reason
                    }
                    for r in evaluation.rule_results
                ],
                "missing_documents": evaluation.missing_documents,
                "fraud_flags": evaluation.fraud_flags
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/applications")
async def list_applications(
    scheme_id: str = None,
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Application)
    
    if scheme_id:
        query = query.filter(Application.scheme_id == scheme_id)
    
    if status:
        query = query.filter(Application.status == status)
    
    applications = query.all()
    
    return [
        {
            "id": app.id,
            "scheme_id": app.scheme_id,
            "applicant_id": app.applicant_id,
            "status": app.status,
            "category": app.category,
            "created_at": app.created_at,
            "updated_at": app.updated_at
        }
        for app in applications
    ]