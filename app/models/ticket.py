from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class TicketCategory(str, enum.Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"
    COMPLAINT = "complaint"

class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Ticket(BaseModel):
    __tablename__ = "tickets"
    
    # Ticket information
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    category = Column(Enum(TicketCategory), nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    
    # Assignment and SLA
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(Text, nullable=True)
    
    # Customer feedback
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 scale
    feedback = Column(Text, nullable=True)
    
    # Foreign keys
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="tickets")
    assigned_user = relationship("User", foreign_keys=[assigned_to], back_populates="tickets_assigned")
    replies = relationship("TicketReply", back_populates="ticket", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ticket(id={self.id}, subject={self.subject}, status={self.status})>"

class TicketReply(BaseModel):
    __tablename__ = "ticket_replies"
    
    # Reply content
    message = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)
    
    # Attachments (store as JSON array of file paths)
    attachments = Column(Text, nullable=True)
    
    # Foreign keys
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="replies")
    user = relationship("User", back_populates="ticket_replies")
    customer = relationship("Customer")
    
    def __repr__(self):
        return f"<TicketReply(ticket_id={self.ticket_id}, is_internal={self.is_internal})>"
