from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.models.customer import Customer
from app.models.enums import TicketStatus
from app.models.ticket import Ticket
from app.models.ticket_message import TicketMessage
from app.models.user import User
from app.schemas.common import Page, PageMeta
from app.schemas.ticket import (
    TicketCreate,
    TicketMessageCreate,
    TicketMessageOut,
    TicketOut,
)
from app.services.audit_service import AuditService

router = APIRouter()


def _scoped_ticket(db: Session, *, ticket_id: uuid.UUID, current: User) -> Ticket:
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id))
    if not ticket:
        raise NotFoundError("Ticket não encontrado")
    if current.tenant_id is not None and ticket.tenant_id != current.tenant_id:
        raise ForbiddenError("Sem acesso a este ticket")
    return ticket


@router.get("", response_model=Page)
def list_tickets(
    limit: int = 20,
    offset: int = 0,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page:
    q = select(Ticket)
    if current.tenant_id is not None:
        q = q.where(Ticket.tenant_id == current.tenant_id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(Ticket.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[TicketOut.model_validate(x) for x in items])


@router.post("", response_model=TicketOut)
def create_ticket(
    payload: TicketCreate,
    request: Request,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketOut:
    if current.tenant_id is None:
        raise ForbiddenError("Usuário sem tenant não pode abrir ticket")
    customer = db.scalar(select(Customer).where(Customer.tenant_id == current.tenant_id, Customer.deleted_at.is_(None)))
    if not customer:
        raise NotFoundError("Cliente não encontrado")
    ticket = Ticket(
        tenant_id=current.tenant_id,
        customer_id=customer.id,
        opened_by_user_id=current.id,
        subject=payload.subject,
        status=TicketStatus.open,
        priority=payload.priority,
        last_message_at=datetime.now(UTC),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    msg = TicketMessage(ticket_id=ticket.id, author_user_id=current.id, is_staff=False, body=payload.message)
    db.add(msg)
    db.commit()

    AuditService(db).log(
        action="ticket.create",
        entity="tickets",
        entity_id=str(ticket.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return TicketOut.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TicketOut:
    ticket = _scoped_ticket(db, ticket_id=ticket_id, current=current)
    return TicketOut.model_validate(ticket)


@router.get("/{ticket_id}/messages", response_model=Page)
def list_messages(
    ticket_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page:
    ticket = _scoped_ticket(db, ticket_id=ticket_id, current=current)
    q = select(TicketMessage).where(TicketMessage.ticket_id == ticket.id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(TicketMessage.created_at.asc()).limit(limit).offset(offset)).all()
    return Page(
        meta=PageMeta(limit=limit, offset=offset, total=total),
        items=[TicketMessageOut.model_validate(x) for x in items],
    )


@router.post("/{ticket_id}/messages", response_model=TicketMessageOut)
def create_message(
    ticket_id: uuid.UUID,
    payload: TicketMessageCreate,
    request: Request,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketMessageOut:
    ticket = _scoped_ticket(db, ticket_id=ticket_id, current=current)
    is_staff = current.tenant_id is None
    msg = TicketMessage(ticket_id=ticket.id, author_user_id=current.id, is_staff=is_staff, body=payload.body)
    ticket.last_message_at = datetime.now(UTC)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    AuditService(db).log(
        action="ticket.message.create",
        entity="ticket_messages",
        entity_id=str(msg.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
        metadata={"ticket_id": str(ticket.id)},
    )
    return TicketMessageOut.model_validate(msg)
