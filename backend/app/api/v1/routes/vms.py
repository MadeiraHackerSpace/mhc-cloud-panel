from __future__ import annotations

import asyncio
import re
import uuid
from datetime import UTC, datetime
from urllib.parse import urlencode

import ssl

from fastapi import APIRouter, Depends, Query, Request, WebSocket
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db, get_sessionmaker
from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import TokenPayloadError, decode_token
from app.integrations.proxmox.service import ProxmoxService
from app.models.enums import ServiceActionType, ServiceStatus, VMStatus
from app.models.service import Service
from app.models.service_action import ServiceAction
from app.models.user import User
from app.models.virtual_machine import VirtualMachine
from app.schemas.common import Page, PageMeta
from app.schemas.vm import VMActionRequest, VMOut, VNCProxyOut
from app.services.audit_service import AuditService

router = APIRouter()

_TAG_SPLIT_RE = re.compile(r"[,\s;]+")


def _parse_tags(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {t.strip() for t in _TAG_SPLIT_RE.split(str(raw)) if t.strip()}


def _extract_uuid_from_tags(tags: set[str], prefix: str) -> uuid.UUID | None:
    for t in tags:
        if not t.startswith(prefix):
            continue
        value = t[len(prefix) :].strip()
        if not value:
            continue
        try:
            return uuid.UUID(value)
        except ValueError:
            return None
    return None


def _status_from_qemu(qemu_status: str | None) -> VMStatus:
    if qemu_status == "running":
        return VMStatus.running
    if qemu_status == "stopped":
        return VMStatus.stopped
    return VMStatus.provisioning


def _reconcile_tenant_vms_from_proxmox(db: Session, *, proxmox: ProxmoxService, tenant_id: uuid.UUID) -> None:
    nodes = proxmox.list_nodes()
    for n in nodes:
        node_name = n.get("node")
        if not node_name:
            continue
        qemus = proxmox.adapter.list_qemu(node=node_name)
        for item in qemus:
            try:
                if int(item.get("template") or 0) == 1:
                    continue
                vmid = int(item.get("vmid"))
                name = str(item.get("name") or vmid)
                tags_raw = item.get("tags")
                if not tags_raw:
                    try:
                        cfg = proxmox.adapter.get_qemu_config(node=node_name, vmid=vmid)
                        tags_raw = cfg.get("tags")
                    except Exception:
                        tags_raw = None
                tags = _parse_tags(str(tags_raw) if tags_raw is not None else None)
                if "mhc-cloud-panel" not in tags:
                    continue
                tag_tenant = _extract_uuid_from_tags(tags, "tenant:")
                if tag_tenant != tenant_id:
                    continue
                service_id = _extract_uuid_from_tags(tags, "service:")
                if not service_id:
                    continue
                service = db.scalar(select(Service).where(Service.id == service_id))
                if not service:
                    continue
                vm = db.scalar(select(VirtualMachine).where(VirtualMachine.service_id == service.id))
                if not vm:
                    vm = db.scalar(
                        select(VirtualMachine).where(
                            VirtualMachine.proxmox_node == node_name,
                            VirtualMachine.proxmox_vmid == vmid,
                        )
                    )
                qemu_status = str(item.get("status") or "")
                if not vm:
                    vm = VirtualMachine(
                        tenant_id=tenant_id,
                        service_id=service.id,
                        proxmox_node=node_name,
                        proxmox_vmid=vmid,
                        name=name,
                        status=_status_from_qemu(qemu_status),
                        template_id=None,
                        last_synced_at=datetime.now(UTC),
                    )
                    db.add(vm)
                else:
                    vm.proxmox_node = node_name
                    vm.proxmox_vmid = vmid
                    vm.name = name
                    if vm.status != VMStatus.deleted:
                        vm.status = _status_from_qemu(qemu_status)
                    vm.last_synced_at = datetime.now(UTC)
            except Exception:
                continue


def _get_vm_scoped(db: Session, *, vm_id: uuid.UUID, current: User) -> VirtualMachine:
    vm = db.scalar(select(VirtualMachine).where(VirtualMachine.id == vm_id))
    if not vm:
        raise NotFoundError("VM não encontrada")
    if current.tenant_id is not None and vm.tenant_id != current.tenant_id:
        raise ForbiddenError("Sem acesso a esta VM")
    return vm


def _get_current_user_ws(websocket: WebSocket, *, db: Session) -> User:
    token: str | None = None
    auth = websocket.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    if not token:
        token = websocket.cookies.get("mhc_access_token")
    if not token:
        raise UnauthorizedError("Não autenticado")
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


@router.get("", response_model=Page)
def list_vms(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_deleted: bool = False,
    refresh: bool = False,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page:
    proxmox = None
    if refresh and current.tenant_id is not None:
        proxmox = ProxmoxService.from_settings()
        _reconcile_tenant_vms_from_proxmox(db, proxmox=proxmox, tenant_id=current.tenant_id)
        db.commit()

    q = select(VirtualMachine)
    if current.tenant_id is not None:
        q = q.where(VirtualMachine.tenant_id == current.tenant_id)
    if not include_deleted:
        q = q.where(VirtualMachine.status != VMStatus.deleted)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(VirtualMachine.created_at.desc()).limit(limit).offset(offset)).all()

    if refresh and items:
        proxmox = proxmox or ProxmoxService.from_settings()
        for vm in items:
            if vm.status == VMStatus.deleted:
                continue
            try:
                status = proxmox.current_status(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
                vm.status = _status_from_qemu(status.get("status"))
                vm.last_synced_at = datetime.now(UTC)
            except Exception:
                vm.status = VMStatus.error
                vm.last_synced_at = datetime.now(UTC)
        db.commit()

    return Page(meta=PageMeta(limit=limit, offset=offset, total=total), items=[VMOut.model_validate(x) for x in items])


@router.get("/{vm_id}", response_model=VMOut)
def get_vm(
    vm_id: uuid.UUID,
    refresh: bool = False,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VMOut:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    if refresh and vm.status != VMStatus.deleted:
        proxmox = ProxmoxService.from_settings()
        try:
            status = proxmox.current_status(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
            vm.status = _status_from_qemu(status.get("status"))
            vm.last_synced_at = datetime.now(UTC)
            db.commit()
        except Exception:
            vm.status = VMStatus.error
            vm.last_synced_at = datetime.now(UTC)
            db.commit()
    return VMOut.model_validate(vm)


@router.post("/{vm_id}/start")
def start_vm(
    vm_id: uuid.UUID,
    request: Request,
    payload: VMActionRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    proxmox.start_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    vm.status = VMStatus.running
    vm.last_synced_at = datetime.now(UTC)
    db.add(
        ServiceAction(
            tenant_id=vm.tenant_id,
            service_id=vm.service_id,
            virtual_machine_id=vm.id,
            requested_by_user_id=current.id,
            action=ServiceActionType.start,
            success=True,
            details={},
        )
    )
    db.commit()
    AuditService(db).log(
        action="vm.start",
        entity="virtual_machines",
        entity_id=str(vm.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True}


@router.post("/{vm_id}/stop")
def stop_vm(
    vm_id: uuid.UUID,
    request: Request,
    payload: VMActionRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    proxmox.stop_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    vm.status = VMStatus.stopped
    vm.last_synced_at = datetime.now(UTC)
    db.add(
        ServiceAction(
            tenant_id=vm.tenant_id,
            service_id=vm.service_id,
            virtual_machine_id=vm.id,
            requested_by_user_id=current.id,
            action=ServiceActionType.stop,
            success=True,
            details={},
        )
    )
    db.commit()
    AuditService(db).log(
        action="vm.stop",
        entity="virtual_machines",
        entity_id=str(vm.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True}


@router.post("/{vm_id}/reboot")
def reboot_vm(
    vm_id: uuid.UUID,
    request: Request,
    payload: VMActionRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    proxmox.reboot_vm(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    vm.last_synced_at = datetime.now(UTC)
    db.add(
        ServiceAction(
            tenant_id=vm.tenant_id,
            service_id=vm.service_id,
            virtual_machine_id=vm.id,
            requested_by_user_id=current.id,
            action=ServiceActionType.reboot,
            success=True,
            details={},
        )
    )
    db.commit()
    AuditService(db).log(
        action="vm.reboot",
        entity="virtual_machines",
        entity_id=str(vm.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True}


@router.get("/{vm_id}/status")
def status_vm(vm_id: uuid.UUID, current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    status = proxmox.current_status(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    if vm.status != VMStatus.deleted:
        try:
            vm.status = _status_from_qemu(status.get("status"))
            vm.last_synced_at = datetime.now(UTC)
            db.commit()
        except Exception:
            pass
    return {"ok": True, "status": status}


@router.post("/{vm_id}/cancel")
def cancel_service(
    vm_id: uuid.UUID,
    request: Request,
    payload: VMActionRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not payload.confirm:
        raise ForbiddenError("Confirmação necessária para cancelar")
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    service = db.scalar(select(Service).where(Service.id == vm.service_id))
    if not service:
        raise NotFoundError("Serviço não encontrado")
    if current.tenant_id is not None and service.tenant_id != current.tenant_id:
        raise ForbiddenError("Sem acesso a este serviço")
    service.status = ServiceStatus.cancelled
    service.cancelled_at = datetime.now(UTC)
    db.commit()
    AuditService(db).log(
        action="service.cancel",
        entity="services",
        entity_id=str(service.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return {"ok": True, "status": service.status}


@router.get("/{vm_id}/vnc", response_model=VNCProxyOut)
def get_vnc_proxy(
    vm_id: uuid.UUID,
    request: Request,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    proxmox = ProxmoxService.from_settings()
    proxy = proxmox.create_vnc_proxy(node=vm.proxmox_node, vmid=vm.proxmox_vmid)
    AuditService(db).log(
        action="vm.vnc_proxy",
        entity="virtual_machines",
        entity_id=str(vm.id),
        actor=current,
        tenant_id=current.tenant_id,
        request=request,
    )
    return proxy


@router.websocket("/{vm_id}/vnc/ws")
async def vnc_websocket_proxy(
    websocket: WebSocket,
    vm_id: uuid.UUID,
    port: int,
    vncticket: str,
):
    import websockets as ws_lib

    # 1. Validate parameters BEFORE accept
    if not (5900 <= port <= 5999):
        await websocket.close(code=1008)
        return
    if not vncticket or len(vncticket) > 512:
        await websocket.close(code=1008)
        return

    # 2. Authenticate BEFORE accept
    db = get_sessionmaker()()
    try:
        current = _get_current_user_ws(websocket, db=db)
        vm = _get_vm_scoped(db, vm_id=vm_id, current=current)
    except (UnauthorizedError, ForbiddenError, NotFoundError):
        await websocket.close(code=1008)
        db.close()
        return

    # 3. Only accept after successful auth
    requested = websocket.headers.get("sec-websocket-protocol") or ""
    requested_protocols = {p.strip().lower() for p in requested.split(",") if p.strip()}
    if "binary" in requested_protocols:
        await websocket.accept(subprotocol="binary")
    else:
        await websocket.accept()

    # 4. Continue with the proxy logic
    try:
        settings = ProxmoxService.from_settings().settings
        if not settings.proxmox_host:
            await websocket.close(code=1011)
            return

        host = settings.proxmox_host
        scheme = "wss" if host.scheme == "https" else "ws"  # type: ignore[union-attr]
        hostname = host.host  # type: ignore[union-attr]
        api_port = host.port or 8006  # type: ignore[union-attr]

        ws_url = (
            f"{scheme}://{hostname}:{api_port}/api2/json/nodes/{vm.proxmox_node}/qemu/{vm.proxmox_vmid}/vncwebsocket?"
            + urlencode({"port": str(port), "vncticket": vncticket})
        )

        auth = f"PVEAPIToken={settings.proxmox_user}@{settings.proxmox_realm}!{settings.proxmox_token_name}={settings.proxmox_token_secret}"

        ssl_ctx = None
        if scheme == "wss":
            ssl_ctx = ssl.create_default_context()
            if not settings.proxmox_verify_ssl:
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

        async with ws_lib.connect(
            ws_url,
            extra_headers={"Authorization": auth},
            ssl=ssl_ctx,
            subprotocols=["binary"],
            max_size=None,
            ping_interval=None,
        ) as upstream:
            async def client_to_upstream():
                while True:
                    message = await websocket.receive()
                    data = message.get("bytes")
                    text = message.get("text")
                    if data is not None:
                        await upstream.send(data)
                    elif text is not None:
                        await upstream.send(text)
                    else:
                        return

            async def upstream_to_client():
                while True:
                    data = await upstream.recv()
                    if isinstance(data, bytes):
                        await websocket.send_bytes(data)
                    else:
                        await websocket.send_text(str(data))

            t1 = asyncio.create_task(client_to_upstream())
            t2 = asyncio.create_task(upstream_to_client())
            done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        try:
            db.close()
        except Exception:
            pass
