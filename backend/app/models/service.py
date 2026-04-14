from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ServiceStatus


class Service(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "services"
    __table_args__ = (
        Index("ix_services_tenant_id", "tenant_id"),
        Index("ix_services_customer_id", "customer_id"),
        Index("ix_services_status", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("plans.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[ServiceStatus] = mapped_column(Enum(ServiceStatus, name="service_status"), default=ServiceStatus.pending, nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(16), default="monthly", nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pending_removal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_period_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")
    customer = relationship("Customer")
    plan = relationship("Plan")
