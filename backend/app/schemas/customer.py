from __future__ import annotations

import uuid

from pydantic import Field

from app.schemas.common import APIModel


class CustomerOut(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    display_name: str
    email: str
    phone: str | None
    document: str | None
    notes: str | None


class CustomerCreate(APIModel):
    display_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    phone: str | None = None
    document: str | None = None
    notes: str | None = None

    admin_user_email: str = Field(min_length=3, max_length=255)
    admin_user_full_name: str = Field(min_length=2, max_length=120)
    admin_user_password: str = Field(min_length=8, max_length=128)
