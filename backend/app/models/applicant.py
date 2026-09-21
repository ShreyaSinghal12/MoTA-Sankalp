from enum import Enum
from sqlalchemy import Column, String, Enum as SQLEnum
from app.models.base import BaseModel

class CategoryEnum(str, Enum):
    ST = "ST"
    SC = "SC"
    OBC = "OBC"
    GENERAL = "GENERAL"

class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class Applicant(BaseModel):
    __tablename__ = "applicants"
    
    external_id = Column(String(100), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    dob = Column(String(10), nullable=False)
    gender = Column(SQLEnum(GenderEnum), nullable=False)
    category = Column(SQLEnum(CategoryEnum), nullable=False)
    pvtg_status = Column(String(50), nullable=True)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    masked_aadhaar = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)