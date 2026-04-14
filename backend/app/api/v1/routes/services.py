from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.integrations.proxmox.service import ProxmoxService
from app.models.customer import Customer
from app.models.enums import InvoiceStatus, JobStatus, ServiceStatus
from app.models.invoice import Invoice
from app.models.job import Job
from app.models.plan import Plan
from app.models.proxmox_node import ProxmoxNode
from app.models.service import Service
from app.models.user import User
from app.schemas.common import Page, PageMeta
from app.schemas.service import ContractPlanRequest, ServiceOut
from app.services.audit_service import AuditService
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
) -> ServiceOut:
    if not payload.confirm:
        raise ForbiddenError("Confirmação necessária para contratar o plano")

    if current.tenant_id is None:
        raise ForbiddenError("Usuário sem tenant não pode contratar planos")

    customer = db.scalar(select(Customer).where(Customer.tenant_id == current.tenant_id, Customer.deleted_at.is_(None)))
    if not customer:
        raise NotFoundError("Cliente não encontrado")

    plan = db.scalar(select(Plan).where(Plan.id == payload.plan_id, Plan.deleted_at.is_(None), Plan.is_active.is_(True)))
    if not plan:
        raise NotFoundError("Plano não encontrado")

    service = Service(
        tenant_id=current.tenant_id,
        customer_id=customer.id,
        plan_id=plan.id,
        name=payload.name,
        status=ServiceStatus.pending,
        billing_cycle=payload.billing_cycle,
    )
    db.add(service)
    db.commit()
    db.refresh(service)

    invoice_number = f"INV-{datetime.now(UTC).strftime('%Y%m%d')}-{str(service.id)[:8]}"
    due_date = datetime.now(UTC) + timedelta(days=3)
    invoice = Invoice(
        tenant_id=service.tenant_id,
        customer_id=customer.id,
        service_id=service.id,
        number=invoice_number,
        status=InvoiceStatus.open,
        amount_total=plan.price_monthly if payload.billing_cycle == "monthly" else (plan.price_quarterly or plan.price_monthly * 3),
        due_date=due_date,
        currency="BRL",
    )
    db.add(invoice)

    node = payload.proxmox_node
    if not node:
        node_row = db.scalar(select(ProxmoxNode).where(ProxmoxNode.is_enabled.is_(True)).order_by(ProxmoxNode.created_at.asc()))
        node = node_row.name if node_row else None
    if not node:
        proxmox = ProxmoxService.from_settings()
        nodes = proxmox.list_nodes()
        node = nodes[0]["node"] if nodes else None
    if not node:
        raise NotFoundError("Nenhum node disponível")

    job_payload: dict = {"proxmox_node": node}
    if payload.template_id:
        job_payload["template_id"] = str(payload.template_id)
    if payload.ipconfig0:
        job_payload["ipconfig0"] = payload.ipconfig0
    if payload.ciuser:
        job_payload["ciuser"] = payload.ciuser
    if payload.ssh_public_key:
        job_payload["ssh_public_key"] = payload.ssh_public_key

    job = Job(
        tenant_id=service.tenant_id,
        service_id=service.id,
        requested_by_user_id=current.id,
        job_key=f"provision:{service.id}",
        job_type="provision_vm",
        status=JobStatus.queued,
        payload=job_payload,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

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
        metadata={"plan_id": str(plan.id), "job_id": str(job.id), "invoice_id": str(invoice.id)},
    )

    return ServiceOut.model_validate(service)
