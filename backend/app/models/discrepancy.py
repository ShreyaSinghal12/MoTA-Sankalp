from enum import Enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class DiscrepancyStatusEnum(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class Discrepancy(BaseModel):
    __tablename__ = "discrepancies"
    
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    type = Column(String(100), nullable=False)
    field_name = Column(String(100), nullable=False)
    expected_value = Column(String(500), nullable=True)
    observed_value = Column(String(500), nullable=True)
    severity = Column(SQLEnum(SeverityEnum), nullable=False)
    status = Column(SQLEnum(DiscrepancyStatusEnum), default=DiscrepancyStatusEnum.OPEN, nullable=False)
    
    application = relationship("Application", backref="discrepancies")

class AgentResolution(BaseModel):
    __tablename__ = "agent_resolutions"
    
    discrepancy_id = Column(Integer, ForeignKey("discrepancies.id"), nullable=False)
    proposed_resolution = Column(Text, nullable=False)
    supporting_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    confidence = Column(String(50), nullable=True)
    status = Column(String(50), default="PROPOSED", nullable=False)
    
    discrepancy = relationship("Discrepancy", backref="resolutions")
    supporting_document = relationship("Document")