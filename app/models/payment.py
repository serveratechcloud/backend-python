from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "bank_transfer"
    VIRTUAL_ACCOUNT = "virtual_account"
    EWALLET = "ewallet"
    CREDIT_CARD = "credit_card"
    CASH = "cash"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(BaseModel):
    __tablename__ = "payments"
    
    # Payment information
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Transaction details
    transaction_id = Column(String(100), nullable=True, index=True)
    bank_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    account_name = Column(String(255), nullable=True)
    
    # Payment gateway response
    gateway_response = Column(Text, nullable=True)
    
    # Timestamps
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(amount={self.amount}, method={self.method}, status={self.status})>"
