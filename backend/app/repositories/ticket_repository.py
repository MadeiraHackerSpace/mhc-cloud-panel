from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.repositories.base import TenantScopedRepository


class TicketRepository(TenantScopedRepository[Ticket]):
    def __init__(self, db: Session, *, tenant_id: uuid.UUID | None) -> None:
        super().__init__(db, tenant_id=tenant_id)

    def list(self, *, limit: int = 20, offset: int = 0) -> tuple[list[Ticket], int]:
        return self._list(Ticket, limit=limit, offset=offset, order_by=Ticket.created_at.desc())

    def get_by_id(self, ticket_id: uuid.UUID) -> Ticket | None:
        return self._get_by_id(Ticket, ticket_id)  # type: ignore[return-value]
