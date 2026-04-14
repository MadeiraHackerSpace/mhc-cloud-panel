from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import VMStatus


class VirtualMachine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "virtual_machines"
    __table_args__ = (
        UniqueConstraint("service_id", name="uq_virtual_machines_service_id"),
        Index("ix_virtual_machines_tenant_id", "tenant_id"),
        Index("ix_virtual_machines_proxmox_node", "proxmox_node"),
        Index("ix_virtual_machines_proxmox_vmid", "proxmox_vmid"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("services.id"), nullable=False)

    proxmox_node: Mapped[str] = mapped_column(String(64), nullable=False)
    proxmox_vmid: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[VMStatus] = mapped_column(Enum(VMStatus, name="vm_status"), default=VMStatus.provisioning, nullable=False)

    primary_ipv4: Mapped[str | None] = mapped_column(String(45), nullable=True)
    primary_ipv6: Mapped[str | None] = mapped_column(String(64), nullable=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("proxmox_templates.id"), nullable=True)

    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    service = relationship("Service")
