from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        *,
        action: str,
        entity: str,
        entity_id: str | None,
        actor: User | None,
        tenant_id: uuid.UUID | None,
        success: bool = True,
        request: Request | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        log = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor.id if actor else None,
            action=action,
            entity=entity,
            entity_id=entity_id,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            meta=metadata or {},
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
