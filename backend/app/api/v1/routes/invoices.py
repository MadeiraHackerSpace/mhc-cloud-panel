from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.models.enums import InvoiceStatus, PaymentStatus, ServiceActionType, ServiceStatus
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.service import Service
from app.models.service_action import ServiceAction
from app.models.user import User
from app.schemas.common import Page, PageMeta
from app.schemas.invoice import InvoiceOut, MarkInvoicePaidRequest
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("", response_model=Page)
def list_invoices(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page:
    q = select(Invoice)
    if current.tenant_id is not None:
        q = q.where(Invoice.tenant_id == current.tenant_id)
    if status:
        try:
            parsed = InvoiceStatus(status)
        except ValueError:
            parsed = None
        if parsed:
            q = q.where(Invoice.status == parsed)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(Invoice.due_date.desc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[InvoiceOut.model_validate(x) for x in items])


@router.post("/{invoice_id}/mark-paid")
def mark_paid(
    invoice_id: uuid.UUID,
    payload: MarkInvoicePaidRequest,
    request: Request,
    current: User = Depends(require_roles("financeiro", "super_admin")),
    db: Session = Depends(get_db),
) -> dict:
    invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id))
    if not invoice:
        raise NotFoundError("Fatura não encontrada")
    if current.tenant_id is not None and invoice.tenant_id != current.tenant_id:
        raise ForbiddenError("Sem acesso a esta fatura")

    invoice.status = InvoiceStatus.paid
    invoice.paid_at = payload.received_at or datetime.now(UTC)
    payment = Payment(
        tenant_id=invoice.tenant_id,
        invoice_id=invoice.id,
        status=PaymentStatus.confirmed,
        amount=invoice.amount_total,
        received_at=invoice.paid_at,
        notes=payload.notes,
        method="manual",
    )
    db.add(payment)

    if invoice.service_id:
        service = db.scalar(select(Service).where(Service.id == invoice.service_id))
        if service and service.status == ServiceStatus.suspended:
            service.status = ServiceStatus.active
            service.suspended_at = None
            db.add(
                ServiceAction(
                    tenant_id=service.tenant_id,
                    service_id=service.id,
                    virtual_machine_id=None,
                    requested_by_user_id=current.id,
                    action=ServiceActionType.reactivate,
                    success=True,
                    details={"invoice_id": str(invoice.id)},
                )
            )

    db.commit()
    AuditService(db).log(
        action="invoice.mark_paid",
        entity="invoices",
        entity_id=str(invoice.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True}
