from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import InvoiceStatus
from app.models.invoice import Invoice
from app.repositories.base import TenantScopedRepository


class InvoiceRepository(TenantScopedRepository[Invoice]):
    def __init__(self, db: Session, *, tenant_id: uuid.UUID | None) -> None:
        super().__init__(db, tenant_id=tenant_id)

    def list(self, *, limit: int = 20, offset: int = 0, status_filter: InvoiceStatus | None = None) -> tuple[list[Invoice], int]:
        extra = []
        if status_filter is not None:
            extra.append(Invoice.status == status_filter)
        return self._list(Invoice, limit=limit, offset=offset, extra_filters=extra or None, order_by=Invoice.due_date.desc())

    def get_by_id(self, invoice_id: uuid.UUID) -> Invoice | None:
        return self._get_by_id(Invoice, invoice_id)  # type: ignore[return-value]

    def mark_paid(self, invoice: Invoice, *, paid_at: datetime | None = None) -> Invoice:
        invoice.status = InvoiceStatus.paid
        invoice.paid_at = paid_at or datetime.now(UTC)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice
