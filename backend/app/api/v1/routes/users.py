from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.core.errors import ForbiddenError
from app.core.security import hash_password
from app.models.user import User
from app.schemas.common import Page, PageMeta
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


@router.get("", response_model=Page)
def list_users(
    limit: int = 20,
    offset: int = 0,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> Page:
    q = select(User).where(User.deleted_at.is_(None))
    if current.tenant_id is not None:
        q = q.where(User.tenant_id == current.tenant_id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(User.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[UserOut.model_validate(x) for x in items])


@router.post("", response_model=UserOut)
def create_user(
    payload: UserCreate,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> UserOut:
    if current.tenant_id is not None and payload.tenant_id not in {None, current.tenant_id}:
        raise ForbiddenError("Não é permitido criar usuário fora do seu tenant")

    user = User(
        tenant_id=payload.tenant_id or current.tenant_id,
        role_id=payload.role_id,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)
