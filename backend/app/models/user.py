from enum import Enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from app.models.base import BaseModel

class RoleEnum(str, Enum):
    MINISTRY_NODAL_OFFICER = "MINISTRY_NODAL_OFFICER"
    STATE_NODAL_OFFICER = "STATE_NODAL_OFFICER"
    DISTRICT_NODAL_OFFICER = "DISTRICT_NODAL_OFFICER"
    SCRUTINY_OFFICER = "SCRUTINY_OFFICER"
    AUDITOR = "AUDITOR"
    ADMIN = "ADMIN"

class User(BaseModel):
    __tablename__ = "users"
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(RoleEnum), nullable=False)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    active = Column(Boolean, default=True, nullable=False)