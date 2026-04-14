from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select

from app.core.database import get_sessionmaker
from app.integrations.proxmox.service import ProxmoxService
from app.models.enums import InvoiceStatus, ServiceActionType, ServiceStatus
from app.models.invoice import Invoice
from app.models.service import Service
from app.models.service_action import ServiceAction
from app.models.virtual_machine import VirtualMachine
from app.tasks.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task
def mark_overdue_and_suspend(grace_days: int = 3) -> dict:
    db = get_sessionmaker()()
    try:
        now = datetime.now(UTC)
        overdue_invoices = db.scalars(select(Invoice).where(Invoice.status == InvoiceStatus.open, Invoice.due_date < now)).all()

        suspended = 0
        proxmox = None
        for inv in overdue_invoices:
            inv.status = InvoiceStatus.overdue
            if not inv.service_id:
                continue
            service = db.scalar(select(Service).where(Service.id == inv.service_id))
            if not service or service.status != ServiceStatus.active:
                continue
            service.status = ServiceStatus.suspended
            service.suspended_at = now
            service.grace_period_ends_at = now + timedelta(days=grace_days)
            vm = db.scalar(select(VirtualMachine).where(VirtualMachine.service_id == service.id))
            if vm:
                try:
                    proxmox = proxmox or ProxmoxService.from_settings()
                    proxmox.stop_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
                except Exception as exc:
                    log.warning("suspend_stop_vm_failed", vm_id=str(vm.id), error=str(exc))
            db.add(
                ServiceAction(
                    tenant_id=service.tenant_id,
                    service_id=service.id,
                    virtual_machine_id=vm.id if vm else None,
                    job_id=None,
                    requested_by_user_id=None,
                    action=ServiceActionType.suspend,
                    success=True,
                    details={"invoice_id": str(inv.id)},
                )
            )
            suspended += 1

        db.commit()
        return {"ok": True, "overdue": len(overdue_invoices), "suspended": suspended}
    finally:
        db.close()
