from __future__ import annotations

import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class PlacementPolicy(str, enum.Enum):
    none = "none"              # NodeScheduler picks best node freely
    affinity = "affinity"      # VMs of same tenant/plan stay on same node
    anti_affinity = "anti_affinity"  # Spread across different nodes (HA)
    pinned = "pinned"          # Reserved for high-performance/dedicated nodes


class Plan(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "plans"
    __table_args__ = (Index("ix_plans_is_active", "is_active"),)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_monthly: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_quarterly: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    vcpu: Mapped[int] = mapped_column(Integer, nullable=False)
    ram_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    disk_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    traffic_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    ipv4_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ipv6_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    snapshots_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backups_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    upgrade_downgrade_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    placement_policy: Mapped[PlacementPolicy] = mapped_column(
        Enum(PlacementPolicy, name="placement_policy"),
        default=PlacementPolicy.none,
        nullable=False,
    )
