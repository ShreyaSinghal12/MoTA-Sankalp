from enum import Enum
from sqlalchemy import Column, String, Integer, ForeignKey, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class DocumentTypeEnum(str, Enum):
    ST_CERTIFICATE = "ST_CERTIFICATE"
    INCOME_CERTIFICATE = "INCOME_CERTIFICATE"
    PG_MARKSHEET = "PG_MARKSHEET"
    ADMISSION_PROOF = "ADMISSION_PROOF"
    BANK_PROOF = "BANK_PROOF"
    IDENTITY_PROOF = "IDENTITY_PROOF"
    OTHER = "OTHER"

class VerificationStatusEnum(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    FLAGGED = "FLAGGED"

class Document(BaseModel):
    __tablename__ = "documents"
    
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    document_type = Column(SQLEnum(DocumentTypeEnum), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=True)
    phash = Column(String(64), nullable=True)
    source = Column(String(50), default="MANUAL", nullable=False)
    verification_status = Column(SQLEnum(VerificationStatusEnum), default=VerificationStatusEnum.PENDING, nullable=False)
    
    application = relationship("Application", backref="documents")

class DocumentExtraction(BaseModel):
    __tablename__ = "document_extractions"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    raw_ocr_text = Column(Text, nullable=True)
    structured_fields = Column(String(2000), nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    layout_detection = Column(String(1000), nullable=True)
    
    document = relationship("Document", backref="extractions")