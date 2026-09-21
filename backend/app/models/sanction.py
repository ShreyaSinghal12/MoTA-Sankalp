from enum import Enum
from sqlalchemy import Column, String, Integer, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class SanctionStatusEnum(str, Enum):
    GENERATED = "GENERATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"

class Sanction(BaseModel):
    __tablename__ = "sanctions"
    
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, unique=True)
    amount = Column(Float, nullable=False)
    sanction_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(SanctionStatusEnum), default=SanctionStatusEnum.GENERATED, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    application = relationship("Application", backref="sanction")
    approver = relationship("User")