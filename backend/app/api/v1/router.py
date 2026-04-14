from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    admin_audit,
    admin_jobs,
    admin_proxmox,
    auth,
    customers,
    invoices,
    plans,
    services,
    tickets,
    users,
    vms,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(vms.router, prefix="/vms", tags=["vms"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])

api_router.include_router(admin_proxmox.router, prefix="/admin/proxmox", tags=["admin/proxmox"])
api_router.include_router(admin_jobs.router, prefix="/admin/jobs", tags=["admin/jobs"])
api_router.include_router(admin_audit.router, prefix="/admin/audit", tags=["admin/audit"])
