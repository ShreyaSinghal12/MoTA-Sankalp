"""SQLAlchemy models. Portable types only (no SQLite-specific features),
so moving to PostgreSQL needs only DATABASE_URL + Alembic later."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # ADMIN | SCRUTINY_OFFICER | ...
    is_active = Column(Boolean, default=True)


class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    application_number = Column(String(50), unique=True, index=True)
    applicant_id = Column(String(50), index=True)  # stable applicant identity (NSP-style)
    full_name = Column(String(255), nullable=False)
    gender = Column(String(10))
    category = Column(String(20), default="ST")
    tribe = Column(String(100))
    is_pvtg = Column(Boolean, default=False)
    state = Column(String(100))
    age = Column(Integer)
    email = Column(String(255))
    phone = Column(String(20))
    scheme_id = Column(String(20), index=True, nullable=False)
    course = Column(String(255))
    institution = Column(String(255))
    annual_income = Column(Float)
    marks_percentage = Column(Float)
    claimed_fee = Column(Float)
    source = Column(String(30), default="PORTAL")  # PORTAL | NSP_IMPORT | SEED
    status = Column(String(30), default="RECEIVED", index=True)
    risk_level = Column(String(20), default="NOT_ASSESSED")
    ai_recommendation = Column(String(40))
    eligibility_score = Column(Float)

    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    doc_type = Column(String(50))
    filename = Column(String(255))
    file_path = Column(String(500))
    content_type = Column(String(100))
    size_bytes = Column(Integer)
    phash = Column(String(64))
    ocr_text = Column(Text)
    ocr_confidence = Column(Float)
    ocr_engine = Column(String(50))
    extracted_fields = Column(JSON)
    detection = Column(JSON)
    processed = Column(Boolean, default=False)

    application = relationship("Application", back_populates="documents")


class RuleResult(Base, TimestampMixin):
    __tablename__ = "rule_results"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    scheme_id = Column(String(20))
    rule_id = Column(String(60))
    description = Column(String(255))
    field = Column(String(60))
    actual_value = Column(String(255))
    expected = Column(String(255))
    passed = Column(Boolean)
    reason = Column(String(500))


class RiskResult(Base, TimestampMixin):
    __tablename__ = "risk_results"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    check_type = Column(String(50))  # NAME_MATCH | DUPLICATE | ANOMALY | DOCUMENT_VISUAL | OCR
    score = Column(Float)
    level = Column(String(20))  # PASS | REVIEW | FLAG
    details = Column(JSON)


class Discrepancy(Base, TimestampMixin):
    __tablename__ = "discrepancies"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    issue_type = Column(String(50))
    severity = Column(String(20))
    description = Column(String(500))
    details = Column(JSON)
    status = Column(String(20), default="OPEN")


class AgentResolution(Base, TimestampMixin):
    __tablename__ = "agent_resolutions"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    discrepancy_id = Column(Integer, ForeignKey("discrepancies.id"), index=True)
    agent = Column(String(50), default="MoTA-Twin v1 (deterministic)")
    issue = Column(String(50))
    proposed_resolution = Column(Text)
    confidence = Column(Float)
    requires_officer_review = Column(Boolean, default=True)
    reasoning = Column(JSON)


class OfficerAction(Base, TimestampMixin):
    __tablename__ = "officer_actions"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    officer_id = Column(Integer, ForeignKey("users.id"))
    officer_email = Column(String(255))
    action = Column(String(30))  # APPROVE | REJECT | MANUAL_REVIEW
    reason = Column(Text)
    ai_recommendation_at_decision = Column(String(40))
    overrode_ai = Column(Boolean, default=False)


class Sanction(Base, TimestampMixin):
    __tablename__ = "sanctions"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True)
    sanction_number = Column(String(60), unique=True)
    amount = Column(Float)
    sanction_date = Column(DateTime(timezone=True), default=utcnow)
    officer_email = Column(String(255))
    status = Column(String(20), default="SANCTIONED")
    pdf_path = Column(String(500))


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    sanction_id = Column(Integer, ForeignKey("sanctions.id"), unique=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    payment_reference = Column(String(60))
    amount = Column(Float)
    status = Column(String(20))
    gateway = Column(String(40), default="PFMS_MOCK")
    response = Column(JSON)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True, nullable=True)
    action = Column(String(60))
    actor = Column(String(255))
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
