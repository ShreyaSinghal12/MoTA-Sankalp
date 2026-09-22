from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import enum

class CategoryEnum(str, enum.Enum):
    ST = "ST"
    SC = "SC"
    OBC = "OBC"
    GENERAL = "GENERAL"
    PVTG = "PVTG"

class StatusEnum(str, enum.Enum):
    RECEIVED = "RECEIVED"
    UNDER_SCRUTINY = "UNDER_SCRUTINY"
    ELIGIBLE = "ELIGIBLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    INELIGIBLE = "INELIGIBLE"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"

class Applicant(Base):
    __tablename__ = "applicants"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)
    category = Column(Enum(CategoryEnum))
    gender = Column(String)
    address = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"))
    scheme_id = Column(String)
    status = Column(Enum(StatusEnum), default=StatusEnum.RECEIVED)
    category = Column(Enum(CategoryEnum))
    age = Column(Integer)
    annual_income = Column(Float)
    qualification = Column(String)
    gender = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
