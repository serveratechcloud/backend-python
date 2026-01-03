from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.user import User
from app.models.customer import Customer, CustomerStatus
from app.models.service import Service, ServiceStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.radius import RadiusSession
from app.api.v1.endpoints.auth import get_current_active_user
from typing import Dict, Any
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics."""
    
    # Customer statistics
    total_customers = db.query(Customer).count()
    active_customers = db.query(Customer).filter(Customer.status == CustomerStatus.ACTIVE).count()
    
    # Service statistics
    active_services = db.query(Service).filter(Service.status == ServiceStatus.ACTIVE).count()
    
    # Revenue statistics
    current_month = datetime.now().replace(day=1)
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.COMPLETED
    ).scalar() or 0
    
    monthly_revenue = db.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.paid_at >= current_month
        )
    ).scalar() or 0
    
    # Invoice statistics
    unpaid_invoices = db.query(Invoice).filter(
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE])
    ).count()
    
    # Online sessions (active RADIUS sessions)
    online_sessions = db.query(RadiusSession).filter(
        RadiusSession.stop_time.is_(None)
    ).count()
    
    # Bandwidth usage (last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    recent_sessions = db.query(RadiusSession).filter(
        or_(
            RadiusSession.start_time >= yesterday,
            and_(
                RadiusSession.start_time < yesterday,
                RadiusSession.stop_time >= yesterday
            )
        )
    ).all()
    
    total_bandwidth = sum(
        (session.input_octets or 0) + (session.output_octets or 0)
        for session in recent_sessions
    )
    
    average_bandwidth = total_bandwidth / len(recent_sessions) if recent_sessions else 0
    
    # Peak bandwidth (highest single session)
    peak_bandwidth = max(
        [(session.input_octets or 0) + (session.output_octets or 0) for session in recent_sessions],
        default=0
    )
    
    return {
        "totalCustomers": total_customers,
        "activeCustomers": active_customers,
        "totalRevenue": float(total_revenue),
        "monthlyRevenue": float(monthly_revenue),
        "unpaidInvoices": unpaid_invoices,
        "onlineSessions": online_sessions,
        "bandwidthUsage": {
            "total": total_bandwidth,
            "average": average_bandwidth,
            "peak": peak_bandwidth
        }
    }

@router.get("/revenue")
async def get_revenue_chart(
    period: str = "monthly",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get revenue chart data."""
    
    if period == "monthly":
        # Last 12 months
        months = []
        revenue_data = []
        
        for i in range(12):
            month_start = (datetime.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            revenue = db.query(func.sum(Payment.amount)).filter(
                and_(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.paid_at >= month_start,
                    Payment.paid_at <= month_end
                )
            ).scalar() or 0
            
            months.append(month_start.strftime("%b %Y"))
            revenue_data.append(float(revenue))
        
        months.reverse()
        revenue_data.reverse()
        
        return {
            "labels": months,
            "datasets": [{
                "label": "Monthly Revenue",
                "data": revenue_data,
                "backgroundColor": "#3b82f6",
                "borderColor": "#2563eb"
            }]
        }
    
    elif period == "daily":
        # Last 30 days
        days = []
        revenue_data = []
        
        for i in range(30):
            day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            revenue = db.query(func.sum(Payment.amount)).filter(
                and_(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.paid_at >= day_start,
                    Payment.paid_at < day_end
                )
            ).scalar() or 0
            
            days.append(day_start.strftime("%d %b"))
            revenue_data.append(float(revenue))
        
        days.reverse()
        revenue_data.reverse()
        
        return {
            "labels": days,
            "datasets": [{
                "label": "Daily Revenue",
                "data": revenue_data,
                "backgroundColor": "#10b981",
                "borderColor": "#059669"
            }]
        }
    
    else:
        raise ValueError("Invalid period. Use 'monthly' or 'daily'")

@router.get("/usage")
async def get_usage_chart(
    period: str = "daily",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get bandwidth usage chart data."""
    
    if period == "daily":
        # Last 7 days
        days = []
        usage_data = []
        
        for i in range(7):
            day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            sessions = db.query(RadiusSession).filter(
                or_(
                    and_(
                        RadiusSession.start_time >= day_start,
                        RadiusSession.start_time < day_end
                    ),
                    and_(
                        RadiusSession.start_time < day_start,
                        RadiusSession.stop_time >= day_start
                    )
                )
            ).all()
            
            total_usage = sum(
                (session.input_octets or 0) + (session.output_octets or 0)
                for session in sessions
            )
            
            days.append(day_start.strftime("%d %b"))
            usage_data.append(total_usage)
        
        days.reverse()
        usage_data.reverse()
        
        return {
            "labels": days,
            "datasets": [{
                "label": "Daily Bandwidth Usage (bytes)",
                "data": usage_data,
                "backgroundColor": "#f59e0b",
                "borderColor": "#d97706"
            }]
        }
    
    elif period == "hourly":
        # Last 24 hours
        hours = []
        usage_data = []
        
        for i in range(24):
            hour_start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            
            sessions = db.query(RadiusSession).filter(
                or_(
                    and_(
                        RadiusSession.start_time >= hour_start,
                        RadiusSession.start_time < hour_end
                    ),
                    and_(
                        RadiusSession.start_time < hour_start,
                        RadiusSession.stop_time >= hour_start
                    )
                )
            ).all()
            
            total_usage = sum(
                (session.input_octets or 0) + (session.output_octets or 0)
                for session in sessions
            )
            
            hours.append(hour_start.strftime("%H:00"))
            usage_data.append(total_usage)
        
        hours.reverse()
        usage_data.reverse()
        
        return {
            "labels": hours,
            "datasets": [{
                "label": "Hourly Bandwidth Usage (bytes)",
                "data": usage_data,
                "backgroundColor": "#ef4444",
                "borderColor": "#dc2626"
            }]
        }
    
    else:
        raise ValueError("Invalid period. Use 'daily' or 'hourly'")
