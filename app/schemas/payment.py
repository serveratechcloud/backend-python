from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from app.models.payment import PaymentMethod, PaymentStatus

class PaymentBase(BaseModel):
    amount: float
    method: PaymentMethod
    transaction_id: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    gateway_response: Optional[str] = None

class Payment(PaymentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    invoice_id: int
    status: PaymentStatus
    gateway_response: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
