from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MFARequiredResponse(BaseModel):
    """Returned when login succeeds but MFA verification is required."""

    mfa_required: Literal[True] = True
    mfa_token: str  # Short-lived JWT (5 min) with type="mfa_pending"


class TOTPEnableResponse(BaseModel):
    """Returned when TOTP setup is initiated."""

    otpauth_uri: str  # For QR code generation
    secret: str  # Base32 secret for manual entry


class TOTPVerifyRequest(BaseModel):
    """Confirm TOTP activation with a valid code."""

    code: str = Field(min_length=6, max_length=6)


class TOTPDisableRequest(BaseModel):
    """Disable TOTP — requires current password and a valid TOTP code."""

    password: str = Field(min_length=8, max_length=128)
    code: str = Field(min_length=6, max_length=6)


class TOTPLoginRequest(BaseModel):
    """Second step of MFA login."""

    mfa_token: str
    code: str = Field(min_length=6, max_length=6)
