from __future__ import annotations

from sqlalchemy import Boolean, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProxmoxNode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "proxmox_nodes"
    __table_args__ = (
        UniqueConstraint("name", name="uq_proxmox_nodes_name"),
        Index("ix_proxmox_nodes_is_enabled", "is_enabled"),
        Index("ix_proxmox_nodes_is_maintenance", "is_maintenance"),
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Maintenance mode: when True, new VMs won't be placed on this node
    # and existing VMs will be drained/migrated by the maintenance_drain task.
    is_maintenance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
