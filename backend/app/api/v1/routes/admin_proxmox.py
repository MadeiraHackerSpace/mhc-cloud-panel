from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.integrations.proxmox.service import ProxmoxService
from app.models.proxmox_node import ProxmoxNode
from app.models.proxmox_storage import ProxmoxStorage
from app.models.proxmox_template import ProxmoxTemplate
from app.models.user import User
from app.schemas.proxmox import ProxmoxNodeInfo, ProxmoxStorageInfo, ProxmoxTemplateInfo

router = APIRouter()


@router.get("/nodes", response_model=list[ProxmoxNodeInfo])
def list_nodes(current: User = Depends(require_roles("super_admin", "operador")), db: Session = Depends(get_db)):
    proxmox = ProxmoxService.from_settings()
    return [ProxmoxNodeInfo.model_validate(x) for x in proxmox.list_nodes()]


@router.get("/storages", response_model=list[ProxmoxStorageInfo])
def list_storages(
    node: str,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
):
    proxmox = ProxmoxService.from_settings()
    return [ProxmoxStorageInfo.model_validate(x) for x in proxmox.list_storages(node=node)]


@router.get("/templates", response_model=list[ProxmoxTemplateInfo])
def list_templates(
    node: str,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
):
    proxmox = ProxmoxService.from_settings()
    items = proxmox.list_templates(node=node)
    return [ProxmoxTemplateInfo(node=node, vmid=int(x["vmid"]), name=str(x.get("name") or x.get("vmid"))) for x in items]


@router.post("/sync")
def sync_metadata(current: User = Depends(require_roles("super_admin", "operador")), db: Session = Depends(get_db)):
    proxmox = ProxmoxService.from_settings()
    nodes = proxmox.list_nodes()
    for n in nodes:
        name = n.get("node")
        if not name:
            continue
        existing = db.scalar(select(ProxmoxNode).where(ProxmoxNode.name == name))
        if not existing:
            db.add(ProxmoxNode(name=name, is_enabled=True))

    db.commit()
    return {"ok": True, "nodes": len(nodes)}
