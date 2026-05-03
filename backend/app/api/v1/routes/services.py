from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_proxmox_service, require_roles
from app.core.database import get_db
from app.core.errors import ForbiddenError
from app.models.service import Service
from app.models.user import User
from app.schemas.common import Page, PageMeta
from app.schemas.service import ContractPlanRequest, ServiceOut
from app.services.audit_service import AuditService
from app.services.contract_service import ContractService
from app.tasks.provision_vm import provision_vm

router = APIRouter()


@router.get("", response_model=Page)
def list_services(
    limit: int = 20,
    offset: int = 0,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page:
    q = select(Service).where(Service.deleted_at.is_(None))
    if current.tenant_id is not None:
        q = q.where(Service.tenant_id == current.tenant_id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(Service.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[ServiceOut.model_validate(x) for x in items])


@router.post("/contract", response_model=ServiceOut)
def contract_plan(
    payload: ContractPlanRequest,
    request: Request,
    current: User = Depends(require_roles("cliente", "operador", "super_admin")),
    db: Session = Depends(get_db),
    proxmox=Depends(get_proxmox_service),
) -> ServiceOut:
    if not payload.confirm:
        raise ForbiddenError("Confirmação necessária para contratar o plano")
    if current.tenant_id is None:
        raise ForbiddenError("Usuário sem tenant não pode contratar planos")

    svc = ContractService(db, proxmox=proxmox)
    service, invoice, job = svc.contract_plan(
        tenant_id=current.tenant_id,
        requested_by_user_id=current.id,
        payload=payload,
    )

    async_result = provision_vm.delay(str(job.id))
    job.celery_task_id = async_result.id
    db.commit()

    AuditService(db).log(
        action="service.contract",
        entity="services",
        entity_id=str(service.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
        metadata={"plan_id": str(service.plan_id), "job_id": str(job.id), "invoice_id": str(invoice.id)},
    )

    return ServiceOut.model_validate(service)
