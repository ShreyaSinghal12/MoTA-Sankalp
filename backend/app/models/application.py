from enum import Enum
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class StatusEnum(str, Enum):
    RECEIVED = "RECEIVED"
    UNDER_SCRUTINY = "UNDER_SCRUTINY"
    DEFECTIVE = "DEFECTIVE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    RECOMMEND_ELIGIBLE = "RECOMMEND_ELIGIBLE"
    RECOMMEND_INELIGIBLE = "RECOMMEND_INELIGIBLE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SANCTIONED = "SANCTIONED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"

class Application(BaseModel):
    __tablename__ = "applications"
    
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)
    scheme_id = Column(String(50), nullable=False)
    academic_year = Column(String(20), nullable=False)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.RECEIVED, nullable=False)
    annual_income = Column(Float, nullable=True)
    marks_percentage = Column(Float, nullable=True)
    institution = Column(String(255), nullable=True)
    submission_date = Column(String(10), nullable=False)
    current_stage = Column(String(100), nullable=False, default="RECEIVED")
    
    applicant = relationship("Applicant", backref="applications")