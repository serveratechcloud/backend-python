from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

class MikroTikDeviceBase(BaseModel):
    name: str
    ip_address: str
    port: int = 8728
    username: str
    password: str
    is_active: bool = True
    is_ssl: bool = False

    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        if v <= 0 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

class MikroTikDeviceCreate(MikroTikDeviceBase):
    pass

class MikroTikDeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_ssl: Optional[bool] = None

class MikroTikDevice(MikroTikDeviceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    last_sync_at: Optional[datetime] = None
    sync_status: str = "unknown"
    version: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
