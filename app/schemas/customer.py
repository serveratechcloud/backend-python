from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import date, datetime
from app.models.customer import CustomerStatus, Gender

class KYCDataBase(BaseModel):
    id_number: str
    id_type: str
    id_expiry: date
    birth_date: date
    gender: Gender
    occupation: str
    company_name: Optional[str] = None
    company_address: Optional[str] = None

class KYCDataCreate(KYCDataBase):
    pass

class KYCDataUpdate(BaseModel):
    id_number: Optional[str] = None
    id_type: Optional[str] = None
    id_expiry: Optional[date] = None
    birth_date: Optional[date] = None
    gender: Optional[Gender] = None
    occupation: Optional[str] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None

class KYCData(KYCDataBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    customer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str
    status: CustomerStatus = CustomerStatus.PENDING

class CustomerCreate(CustomerBase):
    kyc_data: Optional[KYCDataCreate] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[CustomerStatus] = None
    kyc_data: Optional[KYCDataUpdate] = None

class Customer(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    kyc_data: Optional[KYCData] = None
