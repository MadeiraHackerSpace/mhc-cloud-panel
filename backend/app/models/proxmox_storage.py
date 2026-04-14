from __future__ import annotations

from sqlalchemy import Boolean, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProxmoxStorage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "proxmox_storages"
    __table_args__ = (
        UniqueConstraint("name", name="uq_proxmox_storages_name"),
        Index("ix_proxmox_storages_is_enabled", "is_enabled"),
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
