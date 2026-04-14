from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import Field

from app.schemas.common import APIModel


class PlanOut(APIModel):
    id: uuid.UUID
    name: str
    price_monthly: Decimal
    price_quarterly: Decimal | None
    vcpu: int
    ram_mb: int
    disk_gb: int
    traffic_gb: int
    ipv4_count: int
    ipv6_enabled: bool
    snapshots_enabled: bool
    backups_enabled: bool
    upgrade_downgrade_allowed: bool
    is_active: bool


class PlanCreate(APIModel):
    name: str = Field(min_length=2, max_length=120)
    price_monthly: Decimal
    price_quarterly: Decimal | None = None
    vcpu: int = Field(ge=1, le=64)
    ram_mb: int = Field(ge=256, le=1048576)
    disk_gb: int = Field(ge=10, le=10000)
    traffic_gb: int = Field(ge=0, le=100000)
    ipv4_count: int = Field(ge=0, le=16)
    ipv6_enabled: bool = False
    snapshots_enabled: bool = False
    backups_enabled: bool = False
    upgrade_downgrade_allowed: bool = True
    is_active: bool = True
