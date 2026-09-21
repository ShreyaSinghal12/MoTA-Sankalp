from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.applicant import Applicant
from pydantic import BaseModel

router = APIRouter(tags=["applicants"])

class ApplicantCreateSchema(BaseModel):
    name: str
    email: str
    phone: str
    category: str
    gender: str
    address: str

@router.post("/applicants")
async def create_applicant(
    applicant_create: ApplicantCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_applicant = Applicant(
        name=applicant_create.name,
        email=applicant_create.email,
        phone=applicant_create.phone,
        category=applicant_create.category,
        gender=applicant_create.gender,
        address=applicant_create.address
    )
    
    db.add(new_applicant)
    db.commit()
    db.refresh(new_applicant)
    
    return {
        "id": new_applicant.id,
        "name": new_applicant.name,
        "email": new_applicant.email,
        "phone": new_applicant.phone,
        "category": new_applicant.category,
        "gender": new_applicant.gender,
        "message": "Applicant created successfully"
    }

@router.get("/applicants/{applicant_id}")
async def get_applicant(
    applicant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )
    
    return applicant