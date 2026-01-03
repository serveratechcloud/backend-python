from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, customers, services, packages, billing, network, tickets, dashboard, logs

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(packages.router, prefix="/packages", tags=["packages"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(network.router, prefix="/network", tags=["network"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
