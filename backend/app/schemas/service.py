from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import ServiceStatus
from app.schemas.common import APIModel


class ServiceOut(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    name: str
    status: ServiceStatus
    billing_cycle: str
    started_at: datetime | None
    suspended_at: datetime | None
    cancelled_at: datetime | None
    pending_removal_at: datetime | None
    grace_period_ends_at: datetime | None


class ContractPlanRequest(APIModel):
    plan_id: uuid.UUID
    name: str = Field(min_length=2, max_length=120)
    billing_cycle: str = Field(default="monthly", pattern="^(monthly|quarterly)$")
    proxmox_node: str | None = None
    template_id: uuid.UUID | None = None
    ipconfig0: str | None = Field(default=None, max_length=256)
    ciuser: str | None = Field(default=None, max_length=64)
    ssh_public_key: str | None = Field(default=None, max_length=4096)
    confirm: bool = False
