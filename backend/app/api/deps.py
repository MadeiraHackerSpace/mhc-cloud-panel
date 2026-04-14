from __future__ import annotations

from collections.abc import Callable
import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import TokenPayloadError, decode_token
from app.models.role import Role
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if not creds:
        raise UnauthorizedError("Não autenticado")
    token = creds.credentials
    try:
        payload = decode_token(token)
    except TokenPayloadError as exc:
        raise UnauthorizedError(str(exc)) from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Token inválido")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token inválido")

    try:
        parsed_user_id = uuid.UUID(str(user_id))
    except ValueError as exc:
        raise UnauthorizedError("Token inválido") from exc

    user = db.scalar(select(User).where(User.id == parsed_user_id))
    if not user or not user.is_active or user.deleted_at is not None:
        raise UnauthorizedError("Usuário inválido")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed: str) -> Callable[[User], User]:
    def _dep(user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> User:
        role = db.scalar(select(Role).where(Role.id == user.role_id))
        role_name = role.name.value if role else None
        if role_name not in allowed:
            raise ForbiddenError("Sem permissão")
        return user

    return _dep


def tenant_filter_clause(user: User) -> tuple[bool, str | None]:
    return user.tenant_id is None, str(user.tenant_id) if user.tenant_id else None
