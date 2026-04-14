from __future__ import annotations

from sqlalchemy import Boolean, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProxmoxTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "proxmox_templates"
    __table_args__ = (
        UniqueConstraint("name", name="uq_proxmox_templates_name"),
        Index("ix_proxmox_templates_is_enabled", "is_enabled"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    node: Mapped[str] = mapped_column(String(64), nullable=False)
    vmid: Mapped[int] = mapped_column(Integer, nullable=False)
    storage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cloud_init_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
