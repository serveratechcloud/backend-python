from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.service import ServiceStatus

class ServiceBase(BaseModel):
    username: str
    password: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None

class ServiceCreate(ServiceBase):
    customer_id: int
    package_id: int

class ServiceUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    status: Optional[ServiceStatus] = None

class Service(ServiceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    customer_id: int
    package_id: int
    status: ServiceStatus
    activated_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
