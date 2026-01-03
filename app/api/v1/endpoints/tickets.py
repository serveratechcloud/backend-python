from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus, TicketCategory, TicketPriority
from app.models.customer import Customer
from app.schemas.ticket import Ticket as TicketSchema, TicketCreate, TicketUpdate, TicketReply as TicketReplySchema, TicketReplyCreate
from app.api.v1.endpoints.auth import get_current_active_user
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=dict)
async def get_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    assigned_to: Optional[int] = Query(None),
    status: Optional[TicketStatus] = Query(None),
    category: Optional[TicketCategory] = Query(None),
    priority: Optional[TicketPriority] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get tickets with pagination and filtering."""
    
    query = db.query(Ticket)
    
    # Apply filters
    if customer_id:
        query = query.filter(Ticket.customer_id == customer_id)
    
    if assigned_to:
        query = query.filter(Ticket.assigned_to == assigned_to)
    
    if status:
        query = query.filter(Ticket.status == status)
    
    if category:
        query = query.filter(Ticket.category == category)
    
    if priority:
        query = query.filter(Ticket.priority == priority)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    tickets = query.offset(skip).limit(limit).all()
    
    return {
        "data": tickets,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/{ticket_id}", response_model=TicketSchema)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ticket by ID."""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return ticket

@router.post("/", response_model=TicketSchema)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new ticket."""
    
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == ticket_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Create ticket
    db_ticket = Ticket(
        customer_id=ticket_data.customer_id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=ticket_data.category,
        priority=ticket_data.priority,
        status=TicketStatus.OPEN
    )
    
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    logger.info("Ticket created", ticket_id=db_ticket.id, subject=db_ticket.subject)
    
    return db_ticket

@router.put("/{ticket_id}", response_model=TicketSchema)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update ticket."""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Update fields
    update_data = ticket_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(ticket, field, value)
    
    db.commit()
    db.refresh(ticket)
    
    logger.info("Ticket updated", ticket_id=ticket.id)
    
    return ticket

@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete ticket."""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    db.delete(ticket)
    db.commit()
    
    logger.info("Ticket deleted", ticket_id=ticket_id)
    
    return {"message": "Ticket deleted successfully"}

@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign ticket to user."""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    ticket.assigned_to = user_id
    ticket.status = TicketStatus.IN_PROGRESS
    
    db.commit()
    
    logger.info("Ticket assigned", ticket_id=ticket_id, assigned_to=user_id)
    
    return {"message": "Ticket assigned successfully"}

@router.post("/{ticket_id}/replies", response_model=TicketReplySchema)
async def add_ticket_reply(
    ticket_id: int,
    reply_data: TicketReplyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add reply to ticket."""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Create reply
    db_reply = TicketReply(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message=reply_data.message,
        is_internal=reply_data.is_internal
    )
    
    db.add(db_reply)
    db.commit()
    db.refresh(db_reply)
    
    logger.info("Ticket reply added", ticket_id=ticket_id, reply_id=db_reply.id)
    
    return db_reply

@router.get("/{ticket_id}/replies", response_model=List[TicketReplySchema])
async def get_ticket_replies(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all replies for a ticket."""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    from app.models.ticket import TicketReply
    
    replies = db.query(TicketReply).filter(TicketReply.ticket_id == ticket_id).all()
    return replies

@router.post("/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: int,
    resolution: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Resolve ticket."""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    from datetime import datetime
    
    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.utcnow()
    ticket.resolution = resolution
    
    db.commit()
    
    logger.info("Ticket resolved", ticket_id=ticket_id)
    
    return {"message": "Ticket resolved successfully"}

@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Close ticket."""
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    ticket.status = TicketStatus.CLOSED
    
    db.commit()
    
    logger.info("Ticket closed", ticket_id=ticket_id)
    
    return {"message": "Ticket closed successfully"}
