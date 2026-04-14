from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IPAllocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ip_allocations"
    __table_args__ = (
        UniqueConstraint("ip_address", name="uq_ip_allocations_ip_address"),
        Index("ix_ip_allocations_tenant_id", "tenant_id"),
        Index("ix_ip_allocations_service_id", "service_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("services.id"), nullable=False)
    virtual_machine_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("virtual_machines.id"), nullable=True)

    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
