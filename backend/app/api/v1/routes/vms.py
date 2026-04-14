from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.integrations.proxmox.service import ProxmoxService
from app.models.enums import ServiceActionType, ServiceStatus, VMStatus
from app.models.service import Service
from app.models.service_action import ServiceAction
from app.models.user import User
from app.models.virtual_machine import VirtualMachine
from app.schemas.common import Page, PageMeta
from app.schemas.vm import VMActionRequest, VMOut
from app.services.audit_service import AuditService

router = APIRouter()


def _get_vm_scoped(db: Session, *, vm_id: uuid.UUID, current: User) -> VirtualMachine:
    vm = db.scalar(select(VirtualMachine).where(VirtualMachine.id == vm_id))
    if not vm:
        raise NotFoundError("VM não encontrada")
    if current.tenant_id is not None and vm.tenant_id != current.tenant_id:
        raise ForbiddenError("Sem acesso a esta VM")
    return vm


@router.get("", response_model=Page)
def list_vms(
    limit: int = 20,
    offset: int = 0,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page:
    q = select(VirtualMachine)
    if current.tenant_id is not None:
        q = q.where(VirtualMachine.tenant_id == current.tenant_id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(VirtualMachine.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[VMOut.model_validate(x) for x in items])


@router.get("/{vm_id}", response_model=VMOut)
def get_vm(vm_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> VMOut:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    return VMOut.model_validate(vm)


@router.post("/{vm_id}/start")
def start_vm(
    vm_id: uuid.UUID,
    request: Request,
    payload: VMActionRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    proxmox.start_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    vm.status = VMStatus.running
    vm.last_synced_at = datetime.now(UTC)
    db.add(
        ServiceAction(
            tenant_id=vm.tenant_id,
            service_id=vm.service_id,
            virtual_machine_id=vm.id,
            requested_by_user_id=current.id,
            action=ServiceActionType.start,
            success=True,
            details={},
        )
    )
    db.commit()
    AuditService(db).log(
        action="vm.start",
        entity="virtual_machines",
        entity_id=str(vm.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True}


@router.post("/{vm_id}/stop")
def stop_vm(
    vm_id: uuid.UUID,
    request: Request,
    payload: VMActionRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    proxmox.stop_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    vm.status = VMStatus.stopped
    vm.last_synced_at = datetime.now(UTC)
    db.add(
        ServiceAction(
            tenant_id=vm.tenant_id,
            service_id=vm.service_id,
            virtual_machine_id=vm.id,
            requested_by_user_id=current.id,
            action=ServiceActionType.stop,
            success=True,
            details={},
        )
    )
    db.commit()
    AuditService(db).log(
        action="vm.stop",
        entity="virtual_machines",
        entity_id=str(vm.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True}


@router.post("/{vm_id}/reboot")
def reboot_vm(
    vm_id: uuid.UUID,
    request: Request,
    payload: VMActionRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    proxmox.reboot_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    vm.last_synced_at = datetime.now(UTC)
    db.add(
        ServiceAction(
            tenant_id=vm.tenant_id,
            service_id=vm.service_id,
            virtual_machine_id=vm.id,
            requested_by_user_id=current.id,
            action=ServiceActionType.reboot,
            success=True,
            details={},
        )
    )
    db.commit()
    AuditService(db).log(
        action="vm.reboot",
        entity="virtual_machines",
        entity_id=str(vm.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True}


@router.get("/{vm_id}/status")
def status_vm(vm_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    status = proxmox.current_status(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    return {"ok": True, "status": status}


@router.post("/{vm_id}/cancel")
def cancel_service(
    vm_id: uuid.UUID,
    request: Request,
    payload: VMActionRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not payload.confirm:
        raise ForbiddenError("Confirmação necessária para cancelar")
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    service = db.scalar(select(Service).where(Service.id == vm.service_id))
    if not service:
        raise NotFoundError("Serviço não encontrado")
    if current.tenant_id is not None and service.tenant_id != current.tenant_id:
        raise ForbiddenError("Sem acesso a este serviço")
    service.status = ServiceStatus.cancelled
    service.cancelled_at = datetime.now(UTC)
    db.commit()
    AuditService(db).log(
        action="service.cancel",
        entity="services",
        entity_id=str(service.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True, "status": service.status}
