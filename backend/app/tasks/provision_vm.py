from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from celery.exceptions import Retry
from sqlalchemy import select

from app.core.database import get_sessionmaker
from app.integrations.proxmox.service import ProxmoxService, ProxmoxVMCreateSpec
from app.models.enums import JobStatus, ServiceActionType, ServiceStatus, VMStatus
from app.models.job import Job
from app.models.plan import Plan
from app.models.proxmox_template import ProxmoxTemplate
from app.models.service import Service
from app.models.service_action import ServiceAction
from app.models.virtual_machine import VirtualMachine
from app.tasks.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def provision_vm(self, job_id: str) -> dict:
    db = get_sessionmaker()()
    try:
        job = db.scalar(select(Job).where(Job.id == uuid.UUID(job_id)))
        if not job:
            return {"ok": False, "error": "job_not_found"}
        if job.status in {JobStatus.succeeded, JobStatus.running}:
            return {"ok": True, "status": job.status.value}

        job.status = JobStatus.running
        job.started_at = datetime.now(UTC)
        db.commit()

        service = db.scalar(select(Service).where(Service.id == job.service_id))
        if not service:
            raise RuntimeError("service_not_found")
        plan = db.scalar(select(Plan).where(Plan.id == service.plan_id))
        if not plan:
            raise RuntimeError("plan_not_found")

        payload = job.payload or {}
        node = payload.get("proxmox_node")
        template_id = payload.get("template_id")

        if not node:
            raise RuntimeError("node_not_selected")
        template = None
        if template_id:
            template = db.scalar(select(ProxmoxTemplate).where(ProxmoxTemplate.id == uuid.UUID(template_id)))
        if not template:
            template = db.scalar(select(ProxmoxTemplate).where(ProxmoxTemplate.is_enabled.is_(True)))
        if not template:
            raise RuntimeError("template_not_found")

        vm = db.scalar(select(VirtualMachine).where(VirtualMachine.service_id == service.id))
        proxmox = ProxmoxService.from_settings()

        if not vm:
            create_spec = ProxmoxVMCreateSpec(
                name=service.name,
                vcpu=plan.vcpu,
                ram_mb=plan.ram_mb,
                disk_gb=plan.disk_gb,
                node=node,
                template_vmid=template.vmid,
                storage=template.storage,
                tags=[f"tenant:{service.tenant_id}", f"service:{service.id}", "mhc-cloud-panel"],
            )
            new_vmid = proxmox.create_vm_from_template(spec=create_spec)
            vm = VirtualMachine(
                tenant_id=service.tenant_id,
                service_id=service.id,
                proxmox_node=node,
                proxmox_vmid=new_vmid,
                name=service.name,
                status=VMStatus.provisioning,
                template_id=template.id,
            )
            db.add(vm)
            db.commit()
            db.refresh(vm)

        proxmox.start_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)

        vm.status = VMStatus.running
        vm.last_synced_at = datetime.now(UTC)
        service.status = ServiceStatus.active
        service.started_at = service.started_at or datetime.now(UTC)
        db.add(
            ServiceAction(
                tenant_id=service.tenant_id,
                service_id=service.id,
                virtual_machine_id=vm.id,
                job_id=job.id,
                requested_by_user_id=job.requested_by_user_id,
                action=ServiceActionType.provision,
                success=True,
                details={"node": vm.proxmox_node, "vmid": vm.proxmox_vmid},
            )
        )

        job.status = JobStatus.succeeded
        job.finished_at = datetime.now(UTC)
        job.result = {"vm_id": str(vm.id), "proxmox_node": vm.proxmox_node, "proxmox_vmid": vm.proxmox_vmid}
        db.commit()

        return {"ok": True, "vm_id": str(vm.id)}
    except Retry:
        raise
    except Exception as exc:
        try:
            if "job" in locals() and job:
                job.status = JobStatus.failed
                job.finished_at = datetime.now(UTC)
                job.error_message = str(exc)
                db.commit()
        except Exception:
            db.rollback()

        log.exception("provision_vm_failed", job_id=job_id, error=str(exc))
        raise self.retry(exc=exc)
    finally:
        db.close()
