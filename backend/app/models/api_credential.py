from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class APICredential(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "api_credentials"
    __table_args__ = (
        Index("ix_api_credentials_tenant_id", "tenant_id"),
        Index("ix_api_credentials_provider", "provider"),
        Index("ix_api_credentials_is_active", "is_active"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    secret_ciphertext: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
