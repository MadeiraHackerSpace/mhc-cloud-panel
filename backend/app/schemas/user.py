from __future__ import annotations

import uuid

from pydantic import Field

from app.schemas.common import APIModel


class UserOut(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    role_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool


class UserCreate(APIModel):
    tenant_id: uuid.UUID | None = None
    role_id: uuid.UUID
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
