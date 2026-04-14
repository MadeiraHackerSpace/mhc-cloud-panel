from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PlanFeature(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "plan_features"
    __table_args__ = (
        UniqueConstraint("plan_id", "key", name="uq_plan_features_plan_id_key"),
        Index("ix_plan_features_plan_id", "plan_id"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
