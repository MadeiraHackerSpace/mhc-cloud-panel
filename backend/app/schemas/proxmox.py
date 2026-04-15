from __future__ import annotations

from pydantic import BaseModel


class ProxmoxNodeInfo(BaseModel):
    node: str
    status: str | None = None
    maxcpu: int | None = None
    maxmem: int | None = None
    mem: int | None = None


class ProxmoxStorageInfo(BaseModel):
    storage: str
    content: str | None = None
    active: int | None = None
    total: int | None = None
    used: int | None = None


class ProxmoxTemplateInfo(BaseModel):
    node: str
    vmid: int
    name: str


# ── NodeScheduler / capacity schemas ─────────────────────────────────────────


class NodeCapacityOut(BaseModel):
    """Real-time resource snapshot for a single Proxmox node."""

    node: str
    status: str
    mem_used_gb: float
    mem_total_gb: float
    mem_free_gb: float
    mem_free_pct: float
    cpu_usage_pct: float
    maxcpu: int
    disk_used_gb: float
    disk_total_gb: float
    vms_running: int

    model_config = {"from_attributes": True}


class ClusterCapacityOut(BaseModel):
    """Full cluster capacity view with balanciness metric."""

    nodes: list[NodeCapacityOut]
    balanciness: float  # delta % between most/least loaded node
    method: str         # "memory" | "cpu" | "disk"
    online_count: int
    total_count: int


class BestNodeOut(BaseModel):
    """Response for the best-node placement query."""

    node: str
    method: str
    mem_free_gb: float
    cpu_usage_pct: float


class MaintenanceRequest(BaseModel):
    """Payload to set or clear maintenance mode on a node."""

    enable: bool
    notes: str | None = None
    drain: bool = True  # If True, trigger maintenance_drain task immediately

