from __future__ import annotations

import uuid
from datetime import datetime

from app.models.enums import VMStatus
from app.schemas.common import APIModel


class VMOut(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    service_id: uuid.UUID
    proxmox_node: str
    proxmox_vmid: int
    name: str
    status: VMStatus
    primary_ipv4: str | None
    primary_ipv6: str | None
    template_id: uuid.UUID | None
    last_synced_at: datetime | None


class VMActionRequest(APIModel):
    confirm: bool = False


class VNCProxyOut(APIModel):
    ticket: str
    port: int
    upid: str