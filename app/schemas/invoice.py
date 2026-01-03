from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime, date
from app.models.invoice import InvoiceStatus

class InvoiceBase(BaseModel):
    amount: float
    tax_amount: float
    total_amount: float
    due_date: date
    billing_start_date: date
    billing_end_date: date

    @field_validator('amount', 'tax_amount', 'total_amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class InvoiceCreate(InvoiceBase):
    service_id: int

class InvoiceUpdate(BaseModel):
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    billing_start_date: Optional[date] = None
    billing_end_date: Optional[date] = None

class Invoice(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    invoice_number: str
    customer_id: int
    service_id: int
    status: InvoiceStatus
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed properties
    is_overdue: bool
    outstanding_amount: float
