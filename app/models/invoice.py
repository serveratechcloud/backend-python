from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class Invoice(BaseModel):
    __tablename__ = "invoices"
    
    # Invoice information
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Financial information
    amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Status and dates
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Billing period
    billing_start_date = Column(Date, nullable=False)
    billing_end_date = Column(Date, nullable=False)
    
    # Foreign keys
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    service = relationship("Service", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")
    
    def __repr__(self):
        return f"<Invoice(invoice_number={self.invoice_number}, status={self.status})>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        from datetime import date
        return (
            self.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE] and 
            self.due_date < date.today()
        )
    
    @property
    def outstanding_amount(self) -> float:
        """Calculate outstanding amount after payments."""
        total_paid = sum(float(payment.amount) for payment in self.payments 
                        if payment.status == "completed")
        return float(self.total_amount) - total_paid
