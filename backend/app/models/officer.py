from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class OfficerAction(BaseModel):
    __tablename__ = "officer_actions"
    
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    reason = Column(Text, nullable=True)
    
    application = relationship("Application", backref="officer_actions")
    officer = relationship("User")