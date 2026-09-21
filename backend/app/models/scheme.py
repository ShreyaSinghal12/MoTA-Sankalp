from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.models.base import BaseModel
from datetime import datetime

class SchemeConfig(BaseModel):
    __tablename__ = "scheme_configs"
    
    scheme_id = Column(String(50), unique=True, nullable=False)
    scheme_name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(20), nullable=False)
    rules = Column(JSON, nullable=False)
    required_documents = Column(JSON, nullable=False)
    fraud_checks = Column(JSON, nullable=False)
    allocation = Column(JSON, nullable=False)
    is_active = Column(Integer, default=1)
    loaded_at = Column(DateTime, default=datetime.utcnow)