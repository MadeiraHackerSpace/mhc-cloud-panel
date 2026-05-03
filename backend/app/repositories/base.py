from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class TenantScopedRepository(Generic[T]):
    """Base repository that automatically applies tenant_id filtering.

    Security contract:
    - tenant_id=None → super_admin, no filter applied (sees all tenants)
    - tenant_id=<uuid> → scoped to that tenant only, never returns other tenants' data

    All subclasses MUST use _apply_tenant_filter() or _get_by_id() / _list()
    to ensure tenant isolation is enforced by code, not by convention.
    """

    def __init__(self, db: Session, *, tenant_id: uuid.UUID | None) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def _apply_tenant_filter(self, q, model: type) -> object:
        """Apply tenant_id filter to a SQLAlchemy select statement."""
        if self.tenant_id is not None:
            q = q.where(model.tenant_id == self.tenant_id)
        return q

    def _get_by_id(self, model: type, record_id: uuid.UUID) -> object | None:
        """Fetch a single record by ID, scoped to tenant. Returns None if not found or wrong tenant."""
        q = select(model).where(model.id == record_id)
        q = self._apply_tenant_filter(q, model)
        return self.db.scalar(q)

    def _list(
        self,
        model: type,
        *,
        limit: int,
        offset: int,
        extra_filters: list | None = None,
        order_by=None,
    ) -> tuple[list, int]:
        """List records scoped to tenant with pagination. Returns (items, total)."""
        q = select(model)
        q = self._apply_tenant_filter(q, model)
        if extra_filters:
            for f in extra_filters:
                q = q.where(f)
        count_q = select(func.count()).select_from(q.subquery())
        total = self.db.scalar(count_q) or 0
        if order_by is not None:
            q = q.order_by(order_by)
        items = list(self.db.scalars(q.limit(limit).offset(offset)).all())
        return items, total
