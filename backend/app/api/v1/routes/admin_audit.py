from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogOut
from app.schemas.common import Page, PageMeta

router = APIRouter()


@router.get("", response_model=Page)
def list_audit(
    limit: int = 50,
    offset: int = 0,
    action: str | None = None,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> Page:
    q = select(AuditLog)
    if current.tenant_id is not None:
        q = q.where(AuditLog.tenant_id == current.tenant_id)
    if action:
        q = q.where(AuditLog.action == action)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[AuditLogOut.model_validate(x) for x in items])
