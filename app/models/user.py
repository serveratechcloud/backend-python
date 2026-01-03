from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    NETWORK_ADMIN = "network_admin"
    FINANCE_ADMIN = "finance_admin"
    CUSTOMER_SUPPORT = "customer_support"
    RESELLER = "reseller"
    CUSTOMER = "customer"

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    customers = relationship("Customer", back_populates="created_by_user")
    tickets_assigned = relationship("Ticket", foreign_keys="Ticket.assigned_to", back_populates="assigned_user")
    activity_logs = relationship("ActivityLog", back_populates="user")
    ticket_replies = relationship("TicketReply", back_populates="user")
    
    def __repr__(self):
        return f"<User(email={self.email}, role={self.role})>"
