from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel


class AuditLogOut(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    actor_user_id: uuid.UUID | None
    action: str
    entity: str
    entity_id: str | None
    success: bool
    ip_address: str | None
    user_agent: str | None
    metadata: dict = Field(validation_alias="meta", serialization_alias="metadata")
    created_at: datetime
