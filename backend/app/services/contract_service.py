from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.integrations.proxmox.service import ProxmoxService
from app.models.customer import Customer
from app.models.enums import InvoiceStatus, JobStatus, ServiceStatus
from app.models.invoice import Invoice
from app.models.job import Job
from app.models.plan import Plan
from app.models.proxmox_node import ProxmoxNode
from app.models.service import Service
from app.schemas.service import ContractPlanRequest

if TYPE_CHECKING:
    pass

log = structlog.get_logger()


class ContractService:
    """Encapsulates the business logic for contracting a VPS plan.

    Responsibilities:
    - Validate tenant, customer, and plan
    - Create Service, Invoice, and Job records atomically
    - Select the best Proxmox node (delegating to NodeScheduler via provision_vm task)
    - Dispatch the provision_vm Celery task
    """

    def __init__(self, db: Session, *, proxmox: ProxmoxService) -> None:
        self.db = db
        self.proxmox = proxmox

    def contract_plan(
        self,
        *,
        tenant_id: uuid.UUID,
        requested_by_user_id: uuid.UUID,
        payload: ContractPlanRequest,
    ) -> tuple[Service, Invoice, Job]:
        """Create a service contract: Service + Invoice + Job.

        Returns:
            tuple[Service, Invoice, Job]: The created records.

        Raises:
            NotFoundError: If customer, plan, or node is not found.
        """
        customer = self.db.scalar(
            select(Customer).where(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
            )
        )
        if not customer:
            raise NotFoundError("Cliente não encontrado")

        plan = self.db.scalar(
            select(Plan).where(
                Plan.id == payload.plan_id,
                Plan.deleted_at.is_(None),
                Plan.is_active.is_(True),
            )
        )
        if not plan:
            raise NotFoundError("Plano não encontrado")

        service = Service(
            tenant_id=tenant_id,
            customer_id=customer.id,
            plan_id=plan.id,
            name=payload.name,
            status=ServiceStatus.pending,
            billing_cycle=payload.billing_cycle,
        )
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)

        invoice_number = f"INV-{datetime.now(UTC).strftime('%Y%m%d')}-{str(service.id)[:8]}"
        due_date = datetime.now(UTC) + timedelta(days=3)
        amount = (
            plan.price_monthly
            if payload.billing_cycle == "monthly"
            else (plan.price_quarterly or plan.price_monthly * 3)
        )
        invoice = Invoice(
            tenant_id=tenant_id,
            customer_id=customer.id,
            service_id=service.id,
            number=invoice_number,
            status=InvoiceStatus.open,
            amount_total=amount,
            due_date=due_date,
            currency="BRL",
        )
        self.db.add(invoice)

        node = self._resolve_node(payload.proxmox_node)

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
            tenant_id=tenant_id,
            service_id=service.id,
            requested_by_user_id=requested_by_user_id,
            job_key=f"provision:{service.id}",
            job_type="provision_vm",
            status=JobStatus.queued,
            payload=job_payload,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        log.info(
            "contract_service.created",
            service_id=str(service.id),
            invoice_id=str(invoice.id),
            job_id=str(job.id),
            tenant_id=str(tenant_id),
            node=node,
        )

        return service, invoice, job

    def _resolve_node(self, requested_node: str | None) -> str:
        """Resolve the Proxmox node to use for provisioning.

        Priority:
        1. Explicitly requested node (from payload)
        2. First enabled node from DB
        3. First node from live Proxmox API

        Raises:
            NotFoundError: If no node is available.
        """
        if requested_node:
            return requested_node

        node_row = self.db.scalar(
            select(ProxmoxNode)
            .where(ProxmoxNode.is_enabled.is_(True))
            .order_by(ProxmoxNode.created_at.asc())
        )
        if node_row:
            return node_row.name

        nodes = self.proxmox.list_nodes()
        if nodes:
            return nodes[0]["node"]

        raise NotFoundError("Nenhum node disponível")
