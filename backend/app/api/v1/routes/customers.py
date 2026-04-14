from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.core.security import hash_password
from app.models.customer import Customer
from app.models.enums import RoleName
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import Page, PageMeta
from app.schemas.customer import CustomerCreate, CustomerOut
from app.services.audit_service import AuditService
from app.utils.strings import slugify

router = APIRouter()


@router.get("", response_model=Page)
def list_customers(
    limit: int = 20,
    offset: int = 0,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> Page:
    q = select(Customer).where(Customer.deleted_at.is_(None))
    if current.tenant_id is not None:
        q = q.where(Customer.tenant_id == current.tenant_id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(Customer.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[CustomerOut.model_validate(x) for x in items])


@router.post("", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreate,
    request: Request,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> CustomerOut:
    base_slug = slugify(payload.display_name)
    slug = base_slug
    suffix = 1
    while db.scalar(select(Tenant).where(Tenant.slug == slug)) is not None:
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    tenant = Tenant(name=payload.display_name, slug=slug, is_active=True)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    customer = Customer(
        tenant_id=tenant.id,
        display_name=payload.display_name,
        email=payload.email,
        phone=payload.phone,
        document=payload.document,
        notes=payload.notes,
    )
    db.add(customer)

    cliente_role = db.scalar(select(Role).where(Role.name == RoleName.cliente))

    if not cliente_role:
        raise RuntimeError("role_cliente_not_found")

    user = User(
        tenant_id=tenant.id,
        role_id=cliente_role.id,
        email=payload.admin_user_email,
        full_name=payload.admin_user_full_name,
        password_hash=hash_password(payload.admin_user_password),
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(customer)

    AuditService(db).log(
        action="customer.create",
        entity="customers",
        entity_id=str(customer.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
        metadata={"tenant_id": str(tenant.id)},
    )
    return CustomerOut.model_validate(customer)
