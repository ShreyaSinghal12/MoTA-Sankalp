from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class RoleEnum(str, enum.Enum):
    MINISTRY_NODAL_OFFICER = "MINISTRY_NODAL_OFFICER"
    STATE_NODAL_OFFICER = "STATE_NODAL_OFFICER"
    DISTRICT_NODAL_OFFICER = "DISTRICT_NODAL_OFFICER"
    SCRUTINY_OFFICER = "SCRUTINY_OFFICER"
    AUDITOR = "AUDITOR"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(Enum(RoleEnum), default=RoleEnum.SCRUTINY_OFFICER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
