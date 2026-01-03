from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class ServiceStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    PENDING = "pending"

class Service(BaseModel):
    __tablename__ = "services"
    
    # Basic information
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    status = Column(Enum(ServiceStatus), default=ServiceStatus.PENDING, nullable=False)
    
    # Network information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    mac_address = Column(String(17), nullable=True)
    
    # Status timestamps
    activated_at = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    terminated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="services")
    package = relationship("Package", back_populates="services")
    invoices = relationship("Invoice", back_populates="service")
    radius_user = relationship("RadiusUser", back_populates="service", uselist=False)
    
    def __repr__(self):
        return f"<Service(username={self.username}, status={self.status})>"
