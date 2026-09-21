from enum import Enum
from sqlalchemy import Column, String, Integer, ForeignKey, Float, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskResult(BaseModel):
    __tablename__ = "risk_results"
    
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    duplicate_score = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    risk_level = Column(SQLEnum(RiskLevelEnum), nullable=False)
    reason = Column(Text, nullable=True)
    
    application = relationship("Application", backref="risk_results")