from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.customer import Customer, KYCData, CustomerStatus
from app.schemas.customer import Customer as CustomerSchema, CustomerCreate, CustomerUpdate, KYCData as KYCSchema
from app.api.v1.endpoints.auth import get_current_active_user
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=dict)
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[CustomerStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customers with pagination and filtering."""
    
    query = db.query(Customer)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%")
            )
        )
    
    if status:
        query = query.filter(Customer.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    customers = query.offset(skip).limit(limit).all()
    
    return {
        "data": customers,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/{customer_id}", response_model=CustomerSchema)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customer by ID."""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer

@router.post("/", response_model=CustomerSchema)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new customer."""
    
    # Check if email already exists
    existing_customer = db.query(Customer).filter(Customer.email == customer_data.email).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create customer
    db_customer = Customer(
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
        address=customer_data.address,
        status=CustomerStatus.PENDING,
        created_by=current_user.id
    )
    
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    # Create KYC data if provided
    if customer_data.kyc_data:
        kyc_data = KYCData(
            customer_id=db_customer.id,
            **customer_data.kyc_data.model_dump()
        )
        db.add(kyc_data)
        db.commit()
    
    logger.info("Customer created", customer_id=db_customer.id, email=db_customer.email)
    
    return db_customer

@router.put("/{customer_id}", response_model=CustomerSchema)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update customer."""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Update fields
    update_data = customer_data.model_dump(exclude_unset=True, exclude={"kyc_data"})
    
    # Check email uniqueness if updating email
    if "email" in update_data:
        existing_customer = db.query(Customer).filter(
            Customer.email == update_data["email"],
            Customer.id != customer_id
        ).first()
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    # Update KYC data if provided
    if customer_data.kyc_data:
        kyc = db.query(KYCData).filter(KYCData.customer_id == customer_id).first()
        if kyc:
            kyc_update = customer_data.kyc_data.model_dump(exclude_unset=True)
            for field, value in kyc_update.items():
                setattr(kyc, field, value)
        else:
            kyc = KYCData(
                customer_id=customer_id,
                **customer_data.kyc_data.model_dump()
            )
            db.add(kyc)
    
    db.commit()
    db.refresh(customer)
    
    logger.info("Customer updated", customer_id=customer.id)
    
    return customer

@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete customer."""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Check if customer has active services
    from app.models.service import Service, ServiceStatus
    active_services = db.query(Service).filter(
        Service.customer_id == customer_id,
        Service.status.in_([ServiceStatus.ACTIVE, ServiceStatus.SUSPENDED])
    ).count()
    
    if active_services > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete customer with active services"
        )
    
    db.delete(customer)
    db.commit()
    
    logger.info("Customer deleted", customer_id=customer_id)
    
    return {"message": "Customer deleted successfully"}

@router.get("/{customer_id}/services")
async def get_customer_services(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customer's services."""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    from app.models.service import Service
    services = db.query(Service).filter(Service.customer_id == customer_id).all()
    
    return services

@router.post("/{customer_id}/activate")
async def activate_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Activate customer."""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    customer.status = CustomerStatus.ACTIVE
    db.commit()
    
    logger.info("Customer activated", customer_id=customer_id)
    
    return {"message": "Customer activated successfully"}

@router.post("/{customer_id}/suspend")
async def suspend_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Suspend customer."""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    customer.status = CustomerStatus.SUSPENDED
    db.commit()
    
    logger.info("Customer suspended", customer_id=customer_id)
    
    return {"message": "Customer suspended successfully"}
