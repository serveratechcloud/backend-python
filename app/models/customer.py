from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    PENDING = "pending"

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"

class Customer(BaseModel):
    __tablename__ = "customers"
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.PENDING, nullable=False)
    
    # Foreign keys
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    kyc_data = relationship("KYCData", back_populates="customer", uselist=False)
    services = relationship("Service", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    tickets = relationship("Ticket", back_populates="customer")
    ticket_replies = relationship("TicketReply", back_populates="customer")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Customer(name={self.name}, email={self.email})>"

class KYCData(BaseModel):
    __tablename__ = "kyc_data"
    
    # Foreign key
    customer_id = Column(Integer, ForeignKey("customers.id"), unique=True, nullable=False)
    
    # ID information
    id_number = Column(String(50), nullable=False)
    id_type = Column(String(50), nullable=False)
    id_expiry = Column(Date, nullable=False)
    
    # Personal information
    birth_date = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    occupation = Column(String(100), nullable=False)
    
    # Company information (optional)
    company_name = Column(String(255), nullable=True)
    company_address = Column(Text, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="kyc_data")
    
    def __repr__(self):
        return f"<KYCData(customer_id={self.customer_id}, id_number={self.id_number})>"
