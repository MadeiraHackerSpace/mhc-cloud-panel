from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.core.database import get_sessionmaker
from app.integrations.proxmox.service import ProxmoxService
from app.models.enums import VMStatus
from app.models.virtual_machine import VirtualMachine
from app.tasks.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task
def sync_vm_status() -> dict:
    db = get_sessionmaker()()
    try:
        proxmox = ProxmoxService.from_settings()
        vms = db.scalars(select(VirtualMachine)).all()
        updated = 0
        for vm in vms:
            try:
                status = proxmox.current_status(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
                qemu_status = status.get("status")
                if qemu_status == "running":
                    vm.status = VMStatus.running
                elif qemu_status == "stopped":
                    vm.status = VMStatus.stopped
                vm.last_synced_at = datetime.now(UTC)
                updated += 1
            except Exception as exc:
                log.warning("sync_vm_status_item_failed", vm_id=str(vm.id), error=str(exc))
        db.commit()
        return {"ok": True, "updated": updated}
    finally:
        db.close()
