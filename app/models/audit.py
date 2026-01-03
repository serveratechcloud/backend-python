from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"
    
    # Action information
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(100), nullable=False, index=True)
    
    # Request information
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    
    # Additional details (JSON)
    details = Column(Text, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    def __repr__(self):
        return f"<ActivityLog(action={self.action}, resource={self.resource})>"
