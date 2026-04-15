"""maintenance_drain — Celery task for draining a Proxmox node into maintenance mode.

Inspired by ProxLB Maintenance Mode (https://github.com/credativ/ProxLB).

When an operator sets a ProxmoxNode.is_maintenance = True via the admin API,
this task:
  1. Lists all running VMs on the target node.
  2. For each VM, selects the best alternative node (via NodeScheduler).
  3. Triggers a live migration to that node.
  4. Records each move in ServiceAction + AuditLog.

No new VMs will be scheduled to a node with is_maintenance=True because the
NodeScheduler already filters them out in `_maintenance_node_names()`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_sessionmaker
from app.integrations.proxmox.service import ProxmoxService
from app.models.enums import ServiceActionType, VMStatus
from app.models.proxmox_node import ProxmoxNode
from app.models.service_action import ServiceAction
from app.models.virtual_machine import VirtualMachine
from app.services.node_scheduler import NoAvailableNodeError, NodeScheduler
from app.tasks.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def maintenance_drain(self, node_name: str) -> dict:
    """Drain all running VMs from a node entering maintenance mode.

    Args:
        node_name: The Proxmox node name (must match ProxmoxNode.name in DB).

    Returns:
        Summary dict with migrated VMs and any errors.
    """
    settings = get_settings()
    db = get_sessionmaker()()
    try:
        # Confirm node is still marked maintenance in DB
        node_record = db.scalar(
            select(ProxmoxNode).where(ProxmoxNode.name == node_name)
        )
        if not node_record or not node_record.is_maintenance:
            log.info("maintenance_drain.node_not_in_maintenance", node=node_name)
            return {"ok": True, "skipped": True, "reason": "node_not_in_maintenance"}

        proxmox = ProxmoxService.from_settings()
        scheduler = NodeScheduler(proxmox=proxmox, db=db)

        # Find all running VMs on this node
        vms = db.scalars(
            select(VirtualMachine).where(
                VirtualMachine.proxmox_node == node_name,
                VirtualMachine.status == VMStatus.running,
            )
        ).all()

        if not vms:
            log.info("maintenance_drain.no_vms_to_migrate", node=node_name)
            return {"ok": True, "migrated": 0, "errors": 0}

        migrated = 0
        errors: list[dict] = []

        for vm in vms:
            try:
                target_node = scheduler.best_node(
                    method=settings.scheduler_method,
                    excluded_nodes=[node_name],
                )
            except (NoAvailableNodeError, Exception) as exc:
                log.error(
                    "maintenance_drain.no_target_node",
                    vm_id=str(vm.id),
                    node=node_name,
                    error=str(exc),
                )
                errors.append({"vm_id": str(vm.id), "error": str(exc)})
                continue

            try:
                log.info(
                    "maintenance_drain.migrating",
                    vm_id=str(vm.id),
                    vmid=vm.proxmox_vmid,
                    from_node=node_name,
                    to_node=target_node,
                )
                proxmox.migrate_vm(
                    node=node_name,
                    vmid=vm.proxmox_vmid,
                    target_node=target_node,
                )
                vm.proxmox_node = target_node
                vm.last_synced_at = datetime.now(UTC)

                db.add(
                    ServiceAction(
                        tenant_id=vm.tenant_id,
                        service_id=vm.service_id,
                        virtual_machine_id=vm.id,
                        job_id=None,
                        requested_by_user_id=None,
                        action=ServiceActionType.reboot,  # closest existing action type
                        success=True,
                        details={
                            "maintenance_drain": True,
                            "from_node": node_name,
                            "to_node": target_node,
                        },
                    )
                )
                db.commit()
                migrated += 1

            except Exception as exc:
                log.error(
                    "maintenance_drain.migrate_failed",
                    vm_id=str(vm.id),
                    from_node=node_name,
                    to_node=target_node,
                    error=str(exc),
                )
                db.rollback()
                errors.append({"vm_id": str(vm.id), "to_node": target_node, "error": str(exc)})

        log.info(
            "maintenance_drain.complete",
            node=node_name,
            migrated=migrated,
            errors=len(errors),
        )
        return {"ok": True, "node": node_name, "migrated": migrated, "errors": len(errors), "error_details": errors}

    except Exception as exc:
        log.exception("maintenance_drain.failed", node=node_name, error=str(exc))
        raise self.retry(exc=exc)
    finally:
        db.close()
