from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import VMStatus
from app.models.virtual_machine import VirtualMachine
from app.repositories.base import TenantScopedRepository


class VMRepository(TenantScopedRepository[VirtualMachine]):
    def __init__(self, db: Session, *, tenant_id: uuid.UUID | None) -> None:
        super().__init__(db, tenant_id=tenant_id)

    def list(self, *, limit: int = 20, offset: int = 0, include_deleted: bool = False) -> tuple[list[VirtualMachine], int]:
        extra = [] if include_deleted else [VirtualMachine.status != VMStatus.deleted]
        return self._list(VirtualMachine, limit=limit, offset=offset, extra_filters=extra, order_by=VirtualMachine.created_at.desc())

    def get_by_id(self, vm_id: uuid.UUID) -> VirtualMachine | None:
        return self._get_by_id(VirtualMachine, vm_id)  # type: ignore[return-value]

    def get_by_service_id(self, service_id: uuid.UUID) -> VirtualMachine | None:
        q = select(VirtualMachine).where(VirtualMachine.service_id == service_id)
        q = self._apply_tenant_filter(q, VirtualMachine)
        return self.db.scalar(q)
