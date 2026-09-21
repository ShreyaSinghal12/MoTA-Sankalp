from enum import Enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class PaymentStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Payment(BaseModel):
    __tablename__ = "payments"
    
    sanction_id = Column(Integer, ForeignKey("sanctions.id"), nullable=False)
    payment_reference = Column(String(100), unique=True, nullable=True)
    payment_status = Column(SQLEnum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING, nullable=False)
    
    sanction = relationship("Sanction", backref="payments")