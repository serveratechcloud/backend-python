from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"

class QuotaUnit(str, enum.Enum):
    GB = "GB"
    TB = "TB"

class Package(BaseModel):
    __tablename__ = "packages"
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Speed configuration (in Kbps)
    download_speed = Column(Integer, nullable=False)  # Kbps
    upload_speed = Column(Integer, nullable=False)    # Kbps
    
    # Quota configuration (optional)
    quota = Column(Integer, nullable=True)  # in GB or TB
    quota_unit = Column(Enum(QuotaUnit), nullable=True)
    fair_usage_policy = Column(Integer, nullable=True)  # in GB
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0.00, nullable=False)
    
    # Configuration
    billing_cycle = Column(Enum(BillingCycle), default=BillingCycle.MONTHLY, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    services = relationship("Service", back_populates="package")
    
    def __repr__(self):
        return f"<Package(name={self.name}, price={self.price})>"
    
    @property
    def effective_price(self) -> float:
        """Calculate price including tax."""
        return float(self.price) * (1 + float(self.tax_rate) / 100)
    
    @property
    def download_speed_mbps(self) -> float:
        """Get download speed in Mbps."""
        return self.download_speed / 1000
    
    @property
    def upload_speed_mbps(self) -> float:
        """Get upload speed in Mbps."""
        return self.upload_speed / 1000
