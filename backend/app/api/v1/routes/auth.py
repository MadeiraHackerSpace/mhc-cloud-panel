from __future__ import annotations

from typing import Union

from fastapi import APIRouter, Depends, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.errors import UnauthorizedError
from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MFARequiredResponse,
    RefreshRequest,
    TOTPDisableRequest,
    TOTPEnableResponse,
    TOTPLoginRequest,
    TOTPVerifyRequest,
    TokenPair,
)
from app.schemas.user import UserOut
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=Union[TokenPair, MFARequiredResponse])
@limiter.limit("10/minute")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> Union[TokenPair, dict]:
    auth = AuthService(db)
    result = auth.login(email=payload.email, password=payload.password)

    if isinstance(result, dict):
        # MFA required — return the mfa_pending response
        user = db.scalar(select(User).where(User.email == payload.email))
        AuditService(db).log(
            action="login.mfa_required",
            entity="auth",
            entity_id=None,
            actor=user,
            tenant_id=user.tenant_id if user else None,
            request=request,
        )
        return result

    access, refresh = result
    user = db.scalar(select(User).where(User.email == payload.email))
    AuditService(db).log(
        action="login",
        entity="auth",
        entity_id=None,
        actor=user,
        tenant_id=user.tenant_id if user else None,
        request=request,
    )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/totp/login", response_model=TokenPair)
def totp_login(payload: TOTPLoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    """Complete MFA login with TOTP code."""
    auth = AuthService(db)
    access, refresh = auth.totp_login(mfa_token=payload.mfa_token, code=payload.code)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/totp/enable", response_model=TOTPEnableResponse)
def totp_enable(current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TOTPEnableResponse:
    """Initiate TOTP setup. Returns QR code URI and secret for the authenticator app."""
    import pyotp

    secret = pyotp.random_base32()
    current.totp_secret = secret
    # Don't set totp_enabled=True yet — user must verify with a valid code first
    db.commit()

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current.email, issuer_name="MHC Cloud Panel")
    return TOTPEnableResponse(otpauth_uri=uri, secret=secret)


@router.post("/totp/verify")
def totp_verify(
    payload: TOTPVerifyRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Confirm TOTP activation with a valid code. Sets totp_enabled=True."""
    import pyotp

    if not current.totp_secret:
        raise UnauthorizedError("TOTP não foi iniciado. Chame /auth/totp/enable primeiro.")

    totp = pyotp.TOTP(current.totp_secret)
    if not totp.verify(payload.code, valid_window=1):
        raise UnauthorizedError("Código TOTP inválido")

    current.totp_enabled = True
    db.commit()
    return {"ok": True, "totp_enabled": True}


@router.post("/totp/disable")
def totp_disable(
    payload: TOTPDisableRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Disable TOTP. Requires current password and a valid TOTP code."""
    import pyotp

    if not verify_password(payload.password, current.password_hash):
        raise UnauthorizedError("Senha incorreta")

    if not current.totp_enabled or not current.totp_secret:
        raise UnauthorizedError("TOTP não está habilitado")

    totp = pyotp.TOTP(current.totp_secret)
    if not totp.verify(payload.code, valid_window=1):
        raise UnauthorizedError("Código TOTP inválido")

    current.totp_enabled = False
    current.totp_secret = None
    db.commit()
    return {"ok": True, "totp_enabled": False}


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    auth = AuthService(db)
    access, refresh_token = auth.refresh(refresh_token=payload.refresh_token)
    return TokenPair(access_token=access, refresh_token=refresh_token)


@router.post("/logout")
def logout(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    AuthService(db).logout(refresh_token=payload.refresh_token)
    AuditService(db).log(action="logout", entity="auth", entity_id=None, actor=None, tenant_id=None, request=request)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current)
