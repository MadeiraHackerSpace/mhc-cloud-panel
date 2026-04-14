from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import TicketPriority, TicketStatus
from app.schemas.common import APIModel


class TicketOut(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    opened_by_user_id: uuid.UUID
    assigned_to_user_id: uuid.UUID | None
    subject: str
    status: TicketStatus
    priority: TicketPriority
    last_message_at: datetime | None


class TicketCreate(APIModel):
    subject: str = Field(min_length=3, max_length=200)
    priority: TicketPriority = TicketPriority.normal
    message: str = Field(min_length=3, max_length=5000)


class TicketMessageOut(APIModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_user_id: uuid.UUID
    is_staff: bool
    body: str
    created_at: datetime


class TicketMessageCreate(APIModel):
    body: str = Field(min_length=1, max_length=5000)
