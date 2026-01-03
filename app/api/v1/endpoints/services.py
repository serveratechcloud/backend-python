from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.service import Service, ServiceStatus
from app.models.customer import Customer
from app.models.package import Package
from app.schemas.service import Service as ServiceSchema, ServiceCreate, ServiceUpdate
from app.api.v1.endpoints.auth import get_current_active_user
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=dict)
async def get_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    status: Optional[ServiceStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get services with pagination and filtering."""
    
    query = db.query(Service)
    
    # Apply filters
    if customer_id:
        query = query.filter(Service.customer_id == customer_id)
    
    if status:
        query = query.filter(Service.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    services = query.offset(skip).limit(limit).all()
    
    return {
        "data": services,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/{service_id}", response_model=ServiceSchema)
async def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get service by ID."""
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return service

@router.post("/", response_model=ServiceSchema)
async def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new service."""
    
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == service_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Verify package exists
    package = db.query(Package).filter(Package.id == service_data.package_id).first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Check if username already exists
    existing_service = db.query(Service).filter(Service.username == service_data.username).first()
    if existing_service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create service
    db_service = Service(
        customer_id=service_data.customer_id,
        package_id=service_data.package_id,
        username=service_data.username,
        password=service_data.password,
        ip_address=service_data.ip_address,
        mac_address=service_data.mac_address,
        status=ServiceStatus.PENDING
    )
    
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    
    logger.info("Service created", service_id=db_service.id, username=db_service.username)
    
    return db_service

@router.put("/{service_id}", response_model=ServiceSchema)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update service."""
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Update fields
    update_data = service_data.model_dump(exclude_unset=True)
    
    # Check username uniqueness if updating username
    if "username" in update_data:
        existing_service = db.query(Service).filter(
            Service.username == update_data["username"],
            Service.id != service_id
        ).first()
        if existing_service:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    for field, value in update_data.items():
        setattr(service, field, value)
    
    db.commit()
    db.refresh(service)
    
    logger.info("Service updated", service_id=service.id)
    
    return service

@router.delete("/{service_id}")
async def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete service."""
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Check if service has active invoices
    from app.models.invoice import Invoice, InvoiceStatus
    active_invoices = db.query(Invoice).filter(
        Invoice.service_id == service_id,
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE])
    ).count()
    
    if active_invoices > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete service with unpaid invoices"
        )
    
    db.delete(service)
    db.commit()
    
    logger.info("Service deleted", service_id=service_id)
    
    return {"message": "Service deleted successfully"}

@router.post("/{service_id}/activate")
async def activate_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Activate service."""
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    from datetime import datetime
    
    service.status = ServiceStatus.ACTIVE
    service.activated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info("Service activated", service_id=service_id)
    
    return {"message": "Service activated successfully"}

@router.post("/{service_id}/suspend")
async def suspend_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Suspend service."""
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    from datetime import datetime
    
    service.status = ServiceStatus.SUSPENDED
    service.suspended_at = datetime.utcnow()
    
    db.commit()
    
    logger.info("Service suspended", service_id=service_id)
    
    return {"message": "Service suspended successfully"}

@router.post("/{service_id}/terminate")
async def terminate_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Terminate service."""
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    from datetime import datetime
    
    service.status = ServiceStatus.TERMINATED
    service.terminated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info("Service terminated", service_id=service_id)
    
    return {"message": "Service terminated successfully"}
