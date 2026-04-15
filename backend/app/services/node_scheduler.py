"""NodeScheduler — Smart node selection for VM provisioning.

Inspired by ProxLB (https://github.com/credativ/ProxLB).

Responsibilities:
  - Pick the best available Proxmox node for a new VM based on real resource metrics.
  - Protect against overprovisioning (configurable reserve buffer).
  - Respect placement policies defined on the Plan:
      * none         → pick freely by best resource metric
      * affinity     → prefer the node where other tenant VMs already run
      * anti_affinity→ avoid nodes where other tenant VMs run (spread for HA)
      * pinned       → (informational) admin must supply preferred_nodes explicitly
  - Expose cluster capacity summary for the admin API.
  - Compute the cluster "balanciness" (delta between most/least loaded node)
    to drive the rebalance_cluster task.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.virtual_machine import VirtualMachine

if TYPE_CHECKING:
    from app.integrations.proxmox.service import ProxmoxService
    from app.models.plan import PlacementPolicy

log = structlog.get_logger()

# ── Bytes helpers ────────────────────────────────────────────────────────────

_MB = 1024 * 1024
_GB = 1024 * _MB


def _mb_to_bytes(mb: int) -> int:
    return mb * _MB


def _bytes_to_gb(b: int) -> float:
    return round(b / _GB, 2)


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class NodeCapacity:
    """Parsed resource snapshot for a single Proxmox node."""

    node: str
    status: str  # "online" | "offline" | "unknown"
    maxmem: int = 0   # bytes
    mem: int = 0      # bytes used
    maxcpu: int = 0
    cpu: float = 0.0  # fraction 0-1
    maxdisk: int = 0  # bytes (local disk)
    disk: int = 0     # bytes used
    vms_running: int = 0

    # Derived
    @property
    def mem_free(self) -> int:
        return max(self.maxmem - self.mem, 0)

    @property
    def mem_free_pct(self) -> float:
        if not self.maxmem:
            return 0.0
        return round(self.mem_free / self.maxmem * 100, 1)

    @property
    def cpu_used_pct(self) -> float:
        return round(self.cpu * 100, 1)

    @property
    def disk_free(self) -> int:
        return max(self.maxdisk - self.disk, 0)

    @property
    def is_available(self) -> bool:
        return self.status == "online"

    def to_dict(self) -> dict[str, Any]:
        return {
            "node": self.node,
            "status": self.status,
            "mem_used_gb": _bytes_to_gb(self.mem),
            "mem_total_gb": _bytes_to_gb(self.maxmem),
            "mem_free_gb": _bytes_to_gb(self.mem_free),
            "mem_free_pct": self.mem_free_pct,
            "cpu_usage_pct": self.cpu_used_pct,
            "maxcpu": self.maxcpu,
            "disk_used_gb": _bytes_to_gb(self.disk),
            "disk_total_gb": _bytes_to_gb(self.maxdisk),
            "vms_running": self.vms_running,
        }


@dataclass
class ClusterCapacity:
    """Aggregated view of all nodes in the cluster."""

    nodes: list[NodeCapacity] = field(default_factory=list)

    @property
    def online_nodes(self) -> list[NodeCapacity]:
        return [n for n in self.nodes if n.is_available]

    def balanciness(self, method: str = "memory") -> float:
        """Delta (%) between most-loaded and least-loaded online node.

        This is ProxLB's core concept: if balanciness > threshold → rebalance.
        """
        available = self.online_nodes
        if len(available) < 2:
            return 0.0
        if method == "memory":
            usages = [100 - n.mem_free_pct for n in available]
        elif method == "cpu":
            usages = [n.cpu_used_pct for n in available]
        else:
            return 0.0
        return round(max(usages) - min(usages), 1)

    def to_list(self) -> list[dict[str, Any]]:
        return [n.to_dict() for n in self.nodes]


# ── Exceptions ───────────────────────────────────────────────────────────────


class InsufficientCapacityError(Exception):
    """Raised when no node has enough free resources for the requested plan."""


class NoAvailableNodeError(Exception):
    """Raised when no online, non-maintenance node exists."""


# ── NodeScheduler ─────────────────────────────────────────────────────────────


class NodeScheduler:
    """Selects the best Proxmox node for provisioning a new VM.

    Usage:
        scheduler = NodeScheduler(proxmox_service, db_session)
        node_name = scheduler.best_node(ram_mb=2048, vcpu=2, disk_gb=40)
    """

    def __init__(self, proxmox: "ProxmoxService", db: Session | None = None) -> None:
        self.proxmox = proxmox
        self.db = db
        self.settings = get_settings()

    # ── Public API ──────────────────────────────────────────────────────────

    def get_cluster_capacity(self) -> ClusterCapacity:
        """Fetch real-time resource metrics from all Proxmox nodes."""
        raw_nodes = self.proxmox.list_nodes()
        nodes: list[NodeCapacity] = []
        for n in raw_nodes:
            name = n.get("node", "unknown")
            nc = NodeCapacity(
                node=name,
                status=n.get("status", "unknown"),
                maxmem=int(n.get("maxmem") or 0),
                mem=int(n.get("mem") or 0),
                maxcpu=int(n.get("maxcpu") or 0),
                cpu=float(n.get("cpu") or 0.0),
                maxdisk=int(n.get("maxdisk") or 0),
                disk=int(n.get("disk") or 0),
            )
            nodes.append(nc)
        return ClusterCapacity(nodes=nodes)

    def best_node(
        self,
        *,
        ram_mb: int = 0,
        vcpu: int = 0,
        disk_gb: int = 0,
        method: str | None = None,
        placement_policy: "PlacementPolicy | None" = None,
        tenant_id: uuid.UUID | None = None,
        preferred_nodes: list[str] | None = None,
        excluded_nodes: list[str] | None = None,
    ) -> str:
        """Return the name of the best node for placing a new VM.

        Args:
            ram_mb:           RAM required by the plan (MiB).
            vcpu:             vCPU count (used for display; not for filtering).
            disk_gb:          Disk required (GiB).
            method:           "memory" | "cpu" | "disk" (overrides settings).
            placement_policy: From the Plan model; drives affinity logic.
            tenant_id:        Tenant UUID for affinity/anti-affinity resolution.
            preferred_nodes:  Explicit node allow-list (for "pinned" policy).
            excluded_nodes:   Nodes to skip unconditionally.
        """
        from app.models.plan import PlacementPolicy as PP  # local import avoids circular

        method = method or self.settings.scheduler_method
        cluster = self.get_cluster_capacity()
        candidates = cluster.online_nodes

        if not candidates:
            raise NoAvailableNodeError("Nenhum node Proxmox online disponível")

        # Remove explicitly excluded nodes
        if excluded_nodes:
            candidates = [n for n in candidates if n.node not in excluded_nodes]

        # Remove nodes in maintenance mode (checked against DB when available)
        maintenance_names = self._maintenance_node_names()
        if maintenance_names:
            candidates = [n for n in candidates if n.node not in maintenance_names]

        if not candidates:
            raise NoAvailableNodeError("Todos os nodes online estão em manutenção ou excluídos")

        # Apply placement-policy filtering
        policy = placement_policy or PP.none
        if policy == PP.pinned and preferred_nodes:
            pinned = [n for n in candidates if n.node in preferred_nodes]
            if pinned:
                candidates = pinned  # restrict to pinned pool
        elif policy == PP.affinity and tenant_id:
            # _nodes_with_tenant_vms handles db=None by returning empty set
            tenant_nodes = self._nodes_with_tenant_vms(tenant_id)
            affinity_candidates = [n for n in candidates if n.node in tenant_nodes]
            if affinity_candidates:
                candidates = affinity_candidates  # prefer co-location
        elif policy == PP.anti_affinity and tenant_id:
            # _nodes_with_tenant_vms handles db=None by returning empty set
            tenant_nodes = self._nodes_with_tenant_vms(tenant_id)
            spread_candidates = [n for n in candidates if n.node not in tenant_nodes]
            if spread_candidates:
                candidates = spread_candidates  # prefer spread

        # Overprovisioning guard
        if ram_mb > 0:
            ram_bytes_needed = _mb_to_bytes(ram_mb)
            reserve = self.settings.scheduler_reserve_pct / 100
            sufficient = [
                n for n in candidates
                if n.mem_free >= ram_bytes_needed * (1 + reserve)
            ]
            if not sufficient:
                node_summary = ", ".join(
                    f"{n.node}({_bytes_to_gb(n.mem_free):.1f}GB free)"
                    for n in candidates
                )
                raise InsufficientCapacityError(
                    f"Nenhum node tem RAM suficiente para {ram_mb}MB "
                    f"(com buffer de {self.settings.scheduler_reserve_pct}%). "
                    f"Disponível: {node_summary}"
                )
            candidates = sufficient

        # Sort by chosen metric and pick the best
        winner = self._pick_best(candidates, method=method)
        log.info(
            "node_scheduler.best_node",
            selected=winner.node,
            method=method,
            policy=policy,
            ram_mb=ram_mb,
            mem_free_gb=_bytes_to_gb(winner.mem_free),
        )
        return winner.node

    # ── Private helpers ─────────────────────────────────────────────────────

    def _pick_best(self, candidates: list[NodeCapacity], method: str) -> NodeCapacity:
        if method == "memory":
            return max(candidates, key=lambda n: n.mem_free)
        elif method == "cpu":
            return min(candidates, key=lambda n: n.cpu)
        elif method == "disk":
            return max(candidates, key=lambda n: n.disk_free)
        # Fallback: most free memory
        return max(candidates, key=lambda n: n.mem_free)

    def _nodes_with_tenant_vms(self, tenant_id: uuid.UUID) -> set[str]:
        """Return node names where a given tenant already has running VMs."""
        if self.db is None:
            return set()
        rows = self.db.scalars(
            select(VirtualMachine.proxmox_node).where(
                VirtualMachine.tenant_id == tenant_id
            )
        ).all()
        return set(rows)

    def _maintenance_node_names(self) -> set[str]:
        """Return node names currently marked as maintenance in the DB."""
        if self.db is None:
            return set()
        try:
            from app.models.proxmox_node import ProxmoxNode  # local import
            rows = self.db.scalars(
                select(ProxmoxNode.name).where(
                    ProxmoxNode.is_maintenance.is_(True)
                )
            ).all()
            return set(rows)
        except Exception:
            return set()
