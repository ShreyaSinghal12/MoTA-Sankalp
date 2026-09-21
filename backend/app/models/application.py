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
    
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False)
    scheme_id = Column(String(50), nullable=False)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.RECEIVED, nullable=False)
    category = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    annual_income = Column(Float, nullable=False)
    qualification = Column(String(255), nullable=False)
    gender = Column(String(20), nullable=False)
    
    applicant = relationship("Applicant", backref="applications")