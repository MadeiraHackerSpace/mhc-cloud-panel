from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.job import Job
from app.models.enums import JobStatus
from app.models.user import User
from app.schemas.common import Page, PageMeta
from app.schemas.job import JobOut

router = APIRouter()


@router.get("", response_model=Page)
def list_jobs(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    current: User = Depends(require_roles("super_admin", "operador", "suporte", "financeiro")),
    db: Session = Depends(get_db),
) -> Page:
    q = select(Job)
    if current.tenant_id is not None:
        q = q.where(Job.tenant_id == current.tenant_id)
    if status:
        try:
            parsed = JobStatus(status)
        except ValueError:
            parsed = None
        if parsed:
            q = q.where(Job.status == parsed)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(Job.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[JobOut.model_validate(x) for x in items])
