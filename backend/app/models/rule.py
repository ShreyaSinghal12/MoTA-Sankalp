from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class RuleResult(BaseModel):
    __tablename__ = "rule_results"
    
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    rule_code = Column(String(100), nullable=False)
    rule_name = Column(String(255), nullable=False)
    actual_value = Column(String(500), nullable=True)
    expected_condition = Column(String(500), nullable=True)
    result = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=True)
    
    application = relationship("Application", backref="rule_results")