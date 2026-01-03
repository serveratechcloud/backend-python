from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.mikrotik import MikroTikDevice
from app.models.radius import RadiusSession
from app.schemas.mikrotik import MikroTikDevice as DeviceSchema, MikroTikDeviceCreate, MikroTikDeviceUpdate
from app.api.v1.endpoints.auth import get_current_active_user, require_role
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/devices", response_model=List[DeviceSchema])
async def get_mikrotik_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Get all MikroTik devices (network admin only)."""
    
    devices = db.query(MikroTikDevice).all()
    return devices

@router.get("/devices/{device_id}", response_model=DeviceSchema)
async def get_mikrotik_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Get MikroTik device by ID (network admin only)."""
    
    device = db.query(MikroTikDevice).filter(MikroTikDevice.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return device

@router.post("/devices", response_model=DeviceSchema)
async def create_mikrotik_device(
    device_data: MikroTikDeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Create new MikroTik device (network admin only)."""
    
    # Create device
    db_device = MikroTikDevice(
        name=device_data.name,
        ip_address=device_data.ip_address,
        port=device_data.port,
        username=device_data.username,
        password=device_data.password,
        is_active=device_data.is_active,
        is_ssl=device_data.is_ssl
    )
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    logger.info("MikroTik device created", device_id=db_device.id, name=db_device.name)
    
    return db_device

@router.put("/devices/{device_id}", response_model=DeviceSchema)
async def update_mikrotik_device(
    device_id: int,
    device_data: MikroTikDeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Update MikroTik device (network admin only)."""
    
    device = db.query(MikroTikDevice).filter(MikroTikDevice.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Update fields
    update_data = device_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(device, field, value)
    
    db.commit()
    db.refresh(device)
    
    logger.info("MikroTik device updated", device_id=device.id)
    
    return device

@router.delete("/devices/{device_id}")
async def delete_mikrotik_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Delete MikroTik device (network admin only)."""
    
    device = db.query(MikroTikDevice).filter(MikroTikDevice.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    db.delete(device)
    db.commit()
    
    logger.info("MikroTik device deleted", device_id=device_id)
    
    return {"message": "Device deleted successfully"}

@router.get("/sessions")
async def get_active_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Get active RADIUS sessions (network admin only)."""
    
    sessions = db.query(RadiusSession).filter(RadiusSession.stop_time.is_(None)).all()
    return sessions

@router.get("/sessions/all")
async def get_all_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Get all RADIUS sessions (network admin only)."""
    
    sessions = db.query(RadiusSession).all()
    return sessions

@router.post("/disconnect/{username}")
async def disconnect_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Disconnect user session (network admin only)."""
    
    # Find active session for user
    session = db.query(RadiusSession).filter(
        RadiusSession.username == username,
        RadiusSession.stop_time.is_(None)
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found for user"
        )
    
    # Here you would implement actual MikroTik disconnection logic
    # For now, we'll just mark the session as stopped
    
    from datetime import datetime
    
    session.stop_time = datetime.utcnow()
    session.terminate_cause = "Admin-Disconnect"
    
    db.commit()
    
    logger.info("User disconnected", username=username)
    
    return {"message": f"User {username} disconnected successfully"}

@router.post("/devices/{device_id}/sync")
async def sync_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("network_admin"))
):
    """Sync MikroTik device (network admin only)."""
    
    device = db.query(MikroTikDevice).filter(MikroTikDevice.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Here you would implement actual MikroTik sync logic
    # For now, we'll just update the sync timestamp
    
    from datetime import datetime
    
    device.last_sync_at = datetime.utcnow()
    device.sync_status = "synced"
    
    db.commit()
    
    logger.info("Device synced", device_id=device_id)
    
    return {"message": "Device synced successfully"}
