from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from app.models.package import BillingCycle, QuotaUnit

class PackageBase(BaseModel):
    name: str
    description: Optional[str] = None
    download_speed: int  # in Kbps
    upload_speed: int    # in Kbps
    quota: Optional[int] = None
    quota_unit: Optional[QuotaUnit] = None
    fair_usage_policy: Optional[int] = None  # in GB
    price: float
    tax_rate: float = 0.0
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    is_active: bool = True

    @field_validator('download_speed', 'upload_speed')
    @classmethod
    def validate_speed(cls, v):
        if v <= 0:
            raise ValueError('Speed must be greater than 0')
        return v

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

    @field_validator('tax_rate')
    @classmethod
    def validate_tax_rate(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Tax rate must be between 0 and 100')
        return v

    @field_validator('quota')
    @classmethod
    def validate_quota(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Quota must be greater than 0')
        return v

class PackageCreate(PackageBase):
    pass

class PackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    download_speed: Optional[int] = None
    upload_speed: Optional[int] = None
    quota: Optional[int] = None
    quota_unit: Optional[QuotaUnit] = None
    fair_usage_policy: Optional[int] = None
    price: Optional[float] = None
    tax_rate: Optional[float] = None
    billing_cycle: Optional[BillingCycle] = None
    is_active: Optional[bool] = None

class Package(PackageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed properties
    effective_price: float
    download_speed_mbps: float
    upload_speed_mbps: float
