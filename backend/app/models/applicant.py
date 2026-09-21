from enum import Enum
from sqlalchemy import Column, String, Integer
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
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    gender = Column(String(20), nullable=False)
    address = Column(String(500), nullable=True)