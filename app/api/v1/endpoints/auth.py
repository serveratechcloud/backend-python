from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_token, verify_password
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserLogin, UserLoginResponse, UserRefreshToken, User
import structlog

logger = structlog.get_logger()
router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=UserLoginResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens."""
    
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        logger.warning("Login failed - user not found", email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning("Login failed - invalid password", email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning("Login failed - user inactive", email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        subject=user.id, 
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        subject=user.id, 
        expires_delta=refresh_token_expires
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info("User logged in successfully", user_id=user.id, email=user.email)
    
    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=User.model_validate(user)
    )

@router.post("/refresh", response_model=dict)
async def refresh_token(
    token_data: UserRefreshToken,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    
    user_id = verify_token(token_data.refresh_token, token_type="refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, 
        expires_delta=access_token_expires
    )
    
    logger.info("Token refreshed successfully", user_id=user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """Logout user (client-side token removal)."""
    
    # In a production environment, you might want to:
    # 1. Add the token to a blacklist
    # 2. Log the logout event
    # 3. Perform any cleanup
    
    logger.info("User logged out")
    
    return {"message": "Successfully logged out"}

async def get_current_user(
    request: Request,
    credentials: str = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    
    token = credentials.credentials
    user_id = verify_token(token, token_type="access")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def require_role(required_role: str):
    """Decorator to require specific user role."""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role != required_role and current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def require_min_role(min_role_hierarchy: list):
    """Decorator to require minimum role hierarchy."""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        user_role_index = min_role_hierarchy.index(current_user.role)
        if user_role_index < 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
