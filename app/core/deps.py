from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user

def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user and verify admin role."""
    if current_user.role not in ["super_admin", "network_admin", "finance_admin", "customer_support"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def get_super_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user and verify super admin role."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user

def get_network_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user and verify network admin role."""
    if current_user.role not in ["super_admin", "network_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Network admin access required"
        )
    return current_user

def get_finance_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user and verify finance admin role."""
    if current_user.role not in ["super_admin", "finance_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Finance admin access required"
        )
    return current_user

def get_customer_support(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user and verify customer support role."""
    if current_user.role not in ["super_admin", "customer_support"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer support access required"
        )
    return current_user
