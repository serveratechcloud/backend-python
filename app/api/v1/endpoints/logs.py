from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.audit import ActivityLog
from app.api.v1.endpoints.auth import get_current_active_user, require_role
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/activity", response_model=dict)
async def get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin"))
):
    """Get activity logs with pagination and filtering (super admin only)."""
    
    query = db.query(ActivityLog)
    
    # Apply filters
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    if action:
        query = query.filter(ActivityLog.action.ilike(f"%{action}%"))
    
    if resource:
        query = query.filter(ActivityLog.resource.ilike(f"%{resource}%"))
    
    # Order by creation date (newest first)
    query = query.order_by(ActivityLog.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "data": logs,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/activity/{log_id}")
async def get_activity_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin"))
):
    """Get activity log by ID (super admin only)."""
    
    log = db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity log not found"
        )
    
    return log

@router.get("/activity/users/{user_id}")
async def get_user_activity_logs(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get activity logs for specific user (admin or own logs)."""
    
    # Only allow admins to view other users' logs
    if current_user.role not in ["super_admin", "network_admin", "finance_admin", "customer_support"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = db.query(ActivityLog).filter(ActivityLog.user_id == user_id)
    
    # Order by creation date (newest first)
    query = query.order_by(ActivityLog.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "data": logs,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/activity/resources/{resource}")
async def get_resource_activity_logs(
    resource: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    resource_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin"))
):
    """Get activity logs for specific resource (super admin only)."""
    
    query = db.query(ActivityLog).filter(ActivityLog.resource == resource)
    
    if resource_id:
        query = query.filter(ActivityLog.resource_id == resource_id)
    
    # Order by creation date (newest first)
    query = query.order_by(ActivityLog.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "data": logs,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }
