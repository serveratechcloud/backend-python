from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.service import Service
from app.schemas.invoice import Invoice as InvoiceSchema, InvoiceCreate, InvoiceUpdate
from app.schemas.payment import Payment as PaymentSchema, PaymentCreate
from app.api.v1.endpoints.auth import get_current_active_user, require_role
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/invoices", response_model=dict)
async def get_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    status: Optional[InvoiceStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get invoices with pagination and filtering."""
    
    query = db.query(Invoice)
    
    # Apply filters
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    invoices = query.offset(skip).limit(limit).all()
    
    return {
        "data": invoices,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/invoices/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get invoice by ID."""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return invoice

@router.post("/invoices", response_model=InvoiceSchema)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("finance_admin"))
):
    """Create new invoice (finance admin only)."""
    
    # Verify service exists
    service = db.query(Service).filter(Service.id == invoice_data.service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Generate invoice number
    from datetime import datetime
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{service.id:04d}"
    
    # Check if invoice number already exists
    existing_invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()
    if existing_invoice:
        # Generate unique number
        counter = 1
        while existing_invoice:
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{service.id:04d}-{counter:02d}"
            existing_invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()
            counter += 1
    
    # Create invoice
    db_invoice = Invoice(
        invoice_number=invoice_number,
        customer_id=service.customer_id,
        service_id=invoice_data.service_id,
        amount=invoice_data.amount,
        tax_amount=invoice_data.tax_amount,
        total_amount=invoice_data.total_amount,
        status=InvoiceStatus.DRAFT,
        due_date=invoice_data.due_date,
        billing_start_date=invoice_data.billing_start_date,
        billing_end_date=invoice_data.billing_end_date
    )
    
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    logger.info("Invoice created", invoice_id=db_invoice.id, invoice_number=db_invoice.invoice_number)
    
    return db_invoice

@router.put("/invoices/{invoice_id}", response_model=InvoiceSchema)
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("finance_admin"))
):
    """Update invoice (finance admin only)."""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    
    logger.info("Invoice updated", invoice_id=invoice.id)
    
    return invoice

@router.post("/invoices/{invoice_id}/send")
async def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("finance_admin"))
):
    """Send invoice to customer (finance admin only)."""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft invoices can be sent"
        )
    
    invoice.status = InvoiceStatus.SENT
    db.commit()
    
    logger.info("Invoice sent", invoice_id=invoice_id)
    
    return {"message": "Invoice sent successfully"}

@router.post("/invoices/{invoice_id}/pay", response_model=PaymentSchema)
async def record_payment(
    invoice_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("finance_admin"))
):
    """Record payment for invoice (finance admin only)."""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    from datetime import datetime
    
    # Create payment
    db_payment = Payment(
        invoice_id=invoice_id,
        amount=payment_data.amount,
        method=payment_data.method,
        status=PaymentStatus.COMPLETED,
        transaction_id=payment_data.transaction_id,
        bank_name=payment_data.bank_name,
        account_number=payment_data.account_number,
        account_name=payment_data.account_name,
        paid_at=datetime.utcnow()
    )
    
    db.add(db_payment)
    
    # Update invoice status if fully paid
    total_paid = sum(p.amount for p in invoice.payments if p.status == PaymentStatus.COMPLETED) + payment_data.amount
    if total_paid >= float(invoice.total_amount):
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_payment)
    
    logger.info("Payment recorded", payment_id=db_payment.id, invoice_id=invoice_id)
    
    return db_payment

@router.get("/payments", response_model=dict)
async def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    invoice_id: Optional[int] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    method: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payments with pagination and filtering."""
    
    query = db.query(Payment)
    
    # Apply filters
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    
    if status:
        query = query.filter(Payment.status == status)
    
    if method:
        query = query.filter(Payment.method == method)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    payments = query.offset(skip).limit(limit).all()
    
    return {
        "data": payments,
        "pagination": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/payments/{payment_id}", response_model=PaymentSchema)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payment by ID."""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return payment
