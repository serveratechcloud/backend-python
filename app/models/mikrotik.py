from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel

class MikroTikDevice(BaseModel):
    __tablename__ = "mikrotik_devices"
    
    # Device information
    name = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)  # IPv6 compatible
    port = Column(Integer, default=8728, nullable=False)
    
    # Authentication
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_ssl = Column(Boolean, default=False, nullable=False)
    
    # Sync information
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(50), default="unknown", nullable=False)
    
    # Device information
    version = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<MikroTikDevice(name={self.name}, ip_address={self.ip_address})>"
