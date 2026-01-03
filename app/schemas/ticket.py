from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from app.models.ticket import TicketCategory, TicketPriority, TicketStatus

class TicketBase(BaseModel):
    subject: str
    description: str
    category: TicketCategory
    priority: TicketPriority = TicketPriority.MEDIUM

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Subject must be at least 3 characters long')
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters long')
        return v.strip()

class TicketCreate(TicketBase):
    customer_id: int

class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to: Optional[int] = None
    resolution: Optional[str] = None

class Ticket(TicketBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    customer_id: int
    status: TicketStatus
    assigned_to: Optional[int] = None
    sla_deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    satisfaction_rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class TicketReplyBase(BaseModel):
    message: str
    is_internal: bool = False

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Message must be at least 3 characters long')
        return v.strip()

class TicketReplyCreate(TicketReplyBase):
    pass

class TicketReply(TicketReplyBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    ticket_id: int
    user_id: Optional[int] = None
    customer_id: Optional[int] = None
    attachments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
