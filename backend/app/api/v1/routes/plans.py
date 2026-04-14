from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.plan import Plan
from app.models.user import User
from app.schemas.common import Page, PageMeta
from app.schemas.plan import PlanCreate, PlanOut
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("", response_model=Page)
def list_plans(
    limit: int = 20,
    offset: int = 0,
    active_only: bool = True,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page:
    q = select(Plan).where(Plan.deleted_at.is_(None))
    if active_only:
        q = q.where(Plan.is_active.is_(True))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(Plan.price_monthly.asc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[PlanOut.model_validate(x) for x in items])


@router.post("", response_model=PlanOut)
def create_plan(
    payload: PlanCreate,
    request: Request,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> PlanOut:
    plan = Plan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    AuditService(db).log(
        action="plan.create",
        entity="plans",
        entity_id=str(plan.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return PlanOut.model_validate(plan)
