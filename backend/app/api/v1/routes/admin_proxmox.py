from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.proxmox.service import ProxmoxService
from app.models.proxmox_node import ProxmoxNode
from app.models.proxmox_storage import ProxmoxStorage
from app.models.proxmox_template import ProxmoxTemplate
from app.models.user import User
from app.schemas.proxmox import (
    BestNodeOut,
    ClusterCapacityOut,
    MaintenanceRequest,
    NodeCapacityOut,
    ProxmoxNodeInfo,
    ProxmoxStorageInfo,
    ProxmoxTemplateInfo,
)
from app.services.audit_service import AuditService
from app.services.node_scheduler import InsufficientCapacityError, NoAvailableNodeError, NodeScheduler

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


# ── New endpoints: Cluster Capacity, Best-Node, Maintenance ──────────────────


@router.get("/capacity", response_model=ClusterCapacityOut)
def cluster_capacity(
    method: str = "memory",
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> ClusterCapacityOut:
    """Return real-time resource metrics for all Proxmox nodes.

    Inspired by ProxLB's cluster resource collection.
    Supports `method` query param: memory | cpu | disk.
    """
    proxmox = ProxmoxService.from_settings()
    scheduler = NodeScheduler(proxmox=proxmox, db=db)
    cluster = scheduler.get_cluster_capacity()

    nodes_out = [NodeCapacityOut(**n.to_dict()) for n in cluster.nodes]
    return ClusterCapacityOut(
        nodes=nodes_out,
        balanciness=cluster.balanciness(method=method),
        method=method,
        online_count=len(cluster.online_nodes),
        total_count=len(cluster.nodes),
    )


@router.get("/best-node", response_model=BestNodeOut)
def best_node(
    ram_mb: int = 0,
    vcpu: int = 0,
    disk_gb: int = 0,
    method: str | None = None,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> BestNodeOut:
    """Return the best node for a VM placement query.

    Useful for Terraform/Ansible integrations — mirrors ProxLB's --best-node flag.

    Query params:
        ram_mb: RAM required (MiB)
        vcpu:   vCPU count (informational)
        disk_gb: Disk required (GiB)
        method: memory | cpu | disk (default from SCHEDULER_METHOD env var)
    """
    settings = get_settings()
    proxmox = ProxmoxService.from_settings()
    scheduler = NodeScheduler(proxmox=proxmox, db=db)

    try:
        node_name = scheduler.best_node(
            ram_mb=ram_mb,
            vcpu=vcpu,
            disk_gb=disk_gb,
            method=method or settings.scheduler_method,
        )
    except NoAvailableNodeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except InsufficientCapacityError as exc:
        raise HTTPException(status_code=507, detail=str(exc))

    # Fetch fresh metrics to populate the response
    cluster = scheduler.get_cluster_capacity()
    node_data = next((n for n in cluster.nodes if n.node == node_name), None)
    mem_free_gb = node_data.mem_free / (1024 ** 3) if node_data else 0.0
    cpu_pct = node_data.cpu_used_pct if node_data else 0.0

    return BestNodeOut(
        node=node_name,
        method=method or settings.scheduler_method,
        mem_free_gb=round(mem_free_gb, 2),
        cpu_usage_pct=cpu_pct,
    )


@router.post("/nodes/{node_name}/maintenance")
def set_maintenance(
    node_name: str,
    payload: MaintenanceRequest,
    request: Request,
    current: User = Depends(require_roles("super_admin", "operador")),
    db: Session = Depends(get_db),
) -> dict:
    """Enable or disable maintenance mode on a Proxmox node.

    When enabling with drain=True, triggers the maintenance_drain Celery task
    which live-migrates all running VMs to healthy nodes — exactly like ProxLB's
    maintenance mode.
    """
    node_record = db.scalar(select(ProxmoxNode).where(ProxmoxNode.name == node_name))
    if not node_record:
        # Auto-create DB record if it only exists in Proxmox
        node_record = ProxmoxNode(name=node_name, is_enabled=True)
        db.add(node_record)

    node_record.is_maintenance = payload.enable
    if payload.notes is not None:
        node_record.notes = payload.notes
    db.commit()

    AuditService(db).log(
        action="proxmox_node.maintenance" if payload.enable else "proxmox_node.maintenance_cleared",
        entity="proxmox_nodes",
        entity_id=str(node_record.id),
        actor=current,
        tenant_id=None,
        request=request,
    )

    task_id = None
    if payload.enable and payload.drain:
        from app.tasks.maintenance_drain import maintenance_drain  # local import avoids circular
        result = maintenance_drain.delay(node_name)
        task_id = result.id

    return {
        "ok": True,
        "node": node_name,
        "is_maintenance": node_record.is_maintenance,
        "drain_task_id": task_id,
    }

