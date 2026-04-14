from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.models.enums import InvoiceStatus
from app.schemas.common import APIModel


class InvoiceOut(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    service_id: uuid.UUID | None
    number: str
    status: InvoiceStatus
    currency: str
    amount_total: Decimal
    due_date: datetime
    paid_at: datetime | None


class MarkInvoicePaidRequest(APIModel):
    received_at: datetime | None = None
    notes: str | None = None
