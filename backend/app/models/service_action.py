from __future__ import annotations

import uuid

from sqlalchemy import JSON, Enum, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ServiceActionType


class ServiceAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "service_actions"
    __table_args__ = (
        Index("ix_service_actions_tenant_id", "tenant_id"),
        Index("ix_service_actions_service_id", "service_id"),
        Index("ix_service_actions_action", "action"),
        Index("ix_service_actions_created_at", "created_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("services.id"), nullable=False)
    virtual_machine_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("virtual_machines.id"), nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)

    action: Mapped[ServiceActionType] = mapped_column(Enum(ServiceActionType, name="service_action_type"), nullable=False)
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
