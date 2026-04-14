from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TicketMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ticket_messages"
    __table_args__ = (
        Index("ix_ticket_messages_ticket_id", "ticket_id"),
        Index("ix_ticket_messages_created_at", "created_at"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    author_user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
