from __future__ import annotations

from sqlalchemy import Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import RoleName


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("name", name="uq_roles_name"),)

    name: Mapped[RoleName] = mapped_column(Enum(RoleName, name="role_name"), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
