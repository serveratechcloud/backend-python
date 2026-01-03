from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.package import Package, BillingCycle, QuotaUnit
from app.schemas.package import Package as PackageSchema, PackageCreate, PackageUpdate
from app.api.v1.endpoints.auth import get_current_active_user, require_role
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=dict)
async def get_packages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    billing_cycle: Optional[BillingCycle] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get packages with pagination and filtering."""
    
    query = db.query(Package)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(Package.is_active == is_active)
    
    if billing_cycle:
        query = query.filter(Package.billing_cycle == billing_cycle)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    packages = query.offset(skip).limit(limit).all()
    
    return {
        "data": packages,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/{package_id}", response_model=PackageSchema)
async def get_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get package by ID."""
    
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    return package

@router.post("/", response_model=PackageSchema)
async def create_package(
    package_data: PackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Create new package (network admin only)."""
    
    # Create package
    db_package = Package(
        name=package_data.name,
        description=package_data.description,
        download_speed=package_data.download_speed,
        upload_speed=package_data.upload_speed,
        quota=package_data.quota,
        quota_unit=package_data.quota_unit,
        fair_usage_policy=package_data.fair_usage_policy,
        price=package_data.price,
        tax_rate=package_data.tax_rate,
        billing_cycle=package_data.billing_cycle,
        is_active=package_data.is_active
    )
    
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    
    logger.info("Package created", package_id=db_package.id, name=db_package.name)
    
    return db_package

@router.put("/{package_id}", response_model=PackageSchema)
async def update_package(
    package_id: int,
    package_data: PackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Update package (network admin only)."""
    
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Update fields
    update_data = package_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(package, field, value)
    
    db.commit()
    db.refresh(package)
    
    logger.info("Package updated", package_id=package.id)
    
    return package

@router.delete("/{package_id}")
async def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Delete package (network admin only)."""
    
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Check if package has active services
    from app.models.service import Service, ServiceStatus
    active_services = db.query(Service).filter(
        Service.package_id == package_id,
        Service.status.in_([ServiceStatus.ACTIVE, ServiceStatus.SUSPENDED])
    ).count()
    
    if active_services > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete package with active services"
        )
    
    db.delete(package)
    db.commit()
    
    logger.info("Package deleted", package_id=package_id)
    
    return {"message": "Package deleted successfully"}

@router.post("/{package_id}/activate")
async def activate_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Activate package (network admin only)."""
    
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    package.is_active = True
    db.commit()
    
    logger.info("Package activated", package_id=package_id)
    
    return {"message": "Package activated successfully"}

@router.post("/{package_id}/deactivate")
async def deactivate_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Deactivate package (network admin only)."""
    
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    package.is_active = False
    db.commit()
    
    logger.info("Package deactivated", package_id=package_id)
    
    return {"message": "Package deactivated successfully"}
