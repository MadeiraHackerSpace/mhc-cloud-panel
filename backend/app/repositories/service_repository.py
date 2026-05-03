from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import ServiceStatus
from app.models.service import Service
from app.repositories.base import TenantScopedRepository


class ServiceRepository(TenantScopedRepository[Service]):
    def __init__(self, db: Session, *, tenant_id: uuid.UUID | None) -> None:
        super().__init__(db, tenant_id=tenant_id)

    def list(self, *, limit: int = 20, offset: int = 0) -> tuple[list[Service], int]:
        from app.models.service import Service as S
        extra = [S.deleted_at.is_(None)]
        return self._list(Service, limit=limit, offset=offset, extra_filters=extra, order_by=Service.created_at.desc())

    def get_by_id(self, service_id: uuid.UUID) -> Service | None:
        return self._get_by_id(Service, service_id)  # type: ignore[return-value]

    def update_status(self, service: Service, status: ServiceStatus, *, cancelled_at: datetime | None = None) -> Service:
        service.status = status
        if cancelled_at is not None:
            service.cancelled_at = cancelled_at
        self.db.commit()
        self.db.refresh(service)
        return service
