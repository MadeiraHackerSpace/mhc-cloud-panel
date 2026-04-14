from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import UnauthorizedError
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def login(self, *, email: str, password: str) -> tuple[str, str]:
        user = self.db.scalar(select(User).where(User.email == email))
        if not user or not user.is_active or user.deleted_at is not None:
            raise UnauthorizedError("Credenciais inválidas")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Credenciais inválidas")

        role = self.db.scalar(select(Role).where(Role.id == user.role_id))
        role_name = role.name.value if role else "cliente"

        access = create_access_token(subject=str(user.id), tenant_id=str(user.tenant_id) if user.tenant_id else None, role=role_name)
        refresh, jti, exp = create_refresh_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            role=role_name,
        )
        self.db.add(RefreshToken(user_id=user.id, jti=jti, token_hash=hash_token(refresh), expires_at=exp))
        self.db.commit()
        return access, refresh

    def refresh(self, *, refresh_token: str) -> tuple[str, str]:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Token inválido")
        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise UnauthorizedError("Token inválido")

        token_row = self.db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
        if not token_row or token_row.revoked_at is not None or token_row.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Token inválido")
        if token_row.token_hash != hash_token(refresh_token):
            raise UnauthorizedError("Token inválido")

        try:
            parsed_user_id = uuid.UUID(str(user_id))
        except ValueError as exc:
            raise UnauthorizedError("Token inválido") from exc

        user = self.db.scalar(select(User).where(User.id == parsed_user_id))
        if not user or not user.is_active or user.deleted_at is not None:
            raise UnauthorizedError("Usuário inválido")

        role = self.db.scalar(select(Role).where(Role.id == user.role_id))
        role_name = role.name.value if role else "cliente"

        token_row.revoked_at = datetime.now(UTC)
        access = create_access_token(subject=str(user.id), tenant_id=str(user.tenant_id) if user.tenant_id else None, role=role_name)
        new_refresh, new_jti, exp = create_refresh_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            role=role_name,
        )
        self.db.add(RefreshToken(user_id=user.id, jti=new_jti, token_hash=hash_token(new_refresh), expires_at=exp))
        self.db.commit()
        return access, new_refresh

    def logout(self, *, refresh_token: str) -> None:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Token inválido")
        jti = payload.get("jti")
        if not jti:
            raise UnauthorizedError("Token inválido")
        token_row = self.db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
        if token_row and token_row.revoked_at is None:
            token_row.revoked_at = datetime.now(UTC)
            self.db.commit()
