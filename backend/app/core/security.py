from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(*, subject: str, tenant_id: str | None, role: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = _now() + timedelta(minutes=settings.jwt_access_token_expires_minutes)
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "sub": subject,
        "tid": tenant_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": _now(),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(*, subject: str, tenant_id: str | None, role: str, jti: str | None = None) -> tuple[str, str, datetime]:
    settings = get_settings()
    expire = _now() + timedelta(days=settings.jwt_refresh_token_expires_days)
    refresh_jti = jti or secrets.token_urlsafe(24)
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "sub": subject,
        "tid": tenant_id,
        "role": role,
        "type": "refresh",
        "jti": refresh_jti,
        "exp": expire,
        "iat": _now(),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, refresh_jti, expire


class TokenPayloadError(Exception):
    pass


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], issuer=settings.jwt_issuer)
    except JWTError as exc:
        raise TokenPayloadError("Token inválido") from exc
    return payload
