from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserOut
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    auth = AuthService(db)
    access, refresh = auth.login(email=payload.email, password=payload.password)
    user = db.scalar(select(User).where(User.email == payload.email))
    AuditService(db).log(action="login", entity="auth", entity_id=None, actor=user, tenant_id=user.tenant_id if user else None, request=request)
    return TokenPair(access_token=access, refresh_token=refresh)


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
