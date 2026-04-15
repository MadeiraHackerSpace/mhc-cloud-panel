"""Tests for NodeScheduler — smart node selection service.

Tests cover:
  - best_node() selects the node with most free memory (default method)
  - best_node() with CPU method selects least loaded node
  - Overprovisioning guard raises InsufficientCapacityError
  - NoAvailableNodeError when all nodes are offline
  - Maintenance node exclusion
  - Affinity: prefer node where tenant already has VMs
  - Anti-affinity: avoid node where tenant already has VMs
  - ClusterCapacity.balanciness() calculation
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.node_scheduler import (
    ClusterCapacity,
    InsufficientCapacityError,
    NoAvailableNodeError,
    NodeCapacity,
    NodeScheduler,
)

_GB = 1024 ** 3
_MB = 1024 ** 2


def _node(name: str, mem_gb: float, maxmem_gb: float, cpu: float = 0.1, status: str = "online") -> NodeCapacity:
    return NodeCapacity(
        node=name,
        status=status,
        maxmem=int(maxmem_gb * _GB),
        mem=int(mem_gb * _GB),
        maxcpu=8,
        cpu=cpu,
        maxdisk=500 * _GB,
        disk=100 * _GB,
    )


def _make_scheduler(nodes: list[NodeCapacity], db=None) -> NodeScheduler:
    """Build a NodeScheduler with a mocked ProxmoxService returning given nodes."""
    proxmox = MagicMock()
    proxmox.list_nodes.return_value = [
        {
            "node": n.node,
            "status": n.status,
            "mem": n.mem,
            "maxmem": n.maxmem,
            "cpu": n.cpu,
            "maxcpu": n.maxcpu,
            "disk": n.disk,
            "maxdisk": n.maxdisk,
        }
        for n in nodes
    ]
    return NodeScheduler(proxmox=proxmox, db=db)


# ── get_cluster_capacity ──────────────────────────────────────────────────────

class TestGetClusterCapacity:
    def test_parses_nodes(self):
        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        cluster = scheduler.get_cluster_capacity()
        assert len(cluster.nodes) == 2
        assert {n.node for n in cluster.nodes} == {"pve", "pve2"}

    def test_online_count(self):
        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64, status="offline")]
        scheduler = _make_scheduler(nodes)
        cluster = scheduler.get_cluster_capacity()
        assert len(cluster.online_nodes) == 1

    def test_balanciness_memory(self):
        # pve: 4/32 = 12.5% used → 87.5% free
        # pve2: 32/64 = 50% used → 50% free
        # delta loaded = 50 - 12.5 = 37.5%
        nodes = [_node("pve", 4, 32), _node("pve2", 32, 64)]
        scheduler = _make_scheduler(nodes)
        cluster = scheduler.get_cluster_capacity()
        assert cluster.balanciness("memory") == pytest.approx(37.5, abs=0.2)

    def test_balanciness_single_node(self):
        nodes = [_node("pve", 4, 32)]
        scheduler = _make_scheduler(nodes)
        cluster = scheduler.get_cluster_capacity()
        assert cluster.balanciness("memory") == 0.0


# ── best_node ─────────────────────────────────────────────────────────────────

class TestBestNode:
    def test_picks_most_free_memory(self):
        # pve2 has 62GB free vs pve with 28GB free
        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        assert scheduler.best_node(method="memory") == "pve2"

    def test_picks_least_loaded_cpu(self):
        nodes = [_node("pve", 4, 32, cpu=0.8), _node("pve2", 48, 64, cpu=0.05)]
        scheduler = _make_scheduler(nodes)
        assert scheduler.best_node(method="cpu") == "pve2"

    def test_no_available_nodes_raises(self):
        nodes = [_node("pve", 4, 32, status="offline")]
        scheduler = _make_scheduler(nodes)
        with pytest.raises(NoAvailableNodeError):
            scheduler.best_node()

    def test_overprovisioning_guard_raises(self):
        # pve has 1GB free; requesting 20GB — with 10% reserve, we'd need 22GB
        nodes = [_node("pve", 31, 32)]
        scheduler = _make_scheduler(nodes)
        with pytest.raises(InsufficientCapacityError):
            scheduler.best_node(ram_mb=20 * 1024, method="memory")

    def test_overprovisioning_passes_when_enough_free(self):
        # pve2 has 62GB free; requesting 4GB — plenty of room
        nodes = [_node("pve", 31, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        result = scheduler.best_node(ram_mb=4 * 1024, method="memory")
        assert result == "pve2"

    def test_excludes_offline_nodes_from_selection(self):
        nodes = [_node("pve", 4, 32, status="offline"), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        assert scheduler.best_node(method="memory") == "pve2"

    def test_explicit_excluded_nodes(self):
        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        # pve2 has more free, but is excluded — should fall back to pve
        result = scheduler.best_node(method="memory", excluded_nodes=["pve2"])
        assert result == "pve"

    def test_maintenance_node_excluded(self):
        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        # Patch the DB call so pve2 is returned as "in maintenance"
        with patch.object(scheduler, "_maintenance_node_names", return_value={"pve2"}):
            result = scheduler.best_node(method="memory")
        assert result == "pve"

    def test_all_nodes_in_maintenance_raises(self):
        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        with patch.object(scheduler, "_maintenance_node_names", return_value={"pve", "pve2"}):
            with pytest.raises(NoAvailableNodeError):
                scheduler.best_node()


# ── Placement policies ────────────────────────────────────────────────────────

class TestPlacementPolicy:
    def test_affinity_prefers_tenant_node(self):
        import uuid
        from unittest.mock import MagicMock, patch
        from app.models.plan import PlacementPolicy

        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        tenant_id = uuid.uuid4()

        # Replace the methods on the instance with mocks that return fixed sets
        scheduler._nodes_with_tenant_vms = MagicMock(return_value={"pve"})
        scheduler._maintenance_node_names = MagicMock(return_value=set())

        result = scheduler.best_node(
            method="memory",
            placement_policy=PlacementPolicy.affinity,
            tenant_id=tenant_id,
        )
        assert result == "pve", (
            f"Affinity should prefer 'pve' (where tenant already runs), got '{result}'"
        )

    def test_anti_affinity_avoids_tenant_node(self):
        import uuid
        from app.models.plan import PlacementPolicy

        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        tenant_id = uuid.uuid4()

        # pve2 has more free RAM. Anti-affinity avoids pve (where tenant already runs).
        with patch.object(scheduler, "_nodes_with_tenant_vms", return_value={"pve"}):
            result = scheduler.best_node(
                method="memory",
                placement_policy=PlacementPolicy.anti_affinity,
                tenant_id=tenant_id,
            )
        assert result == "pve2"

    def test_pinned_restricts_to_preferred_nodes(self):
        import uuid
        from app.models.plan import PlacementPolicy

        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)

        # pve2 has more free RAM, but pinned restricts to pve only
        result = scheduler.best_node(
            method="memory",
            placement_policy=PlacementPolicy.pinned,
            preferred_nodes=["pve"],
        )
        assert result == "pve"

    def test_none_policy_picks_freely(self):
        from app.models.plan import PlacementPolicy

        nodes = [_node("pve", 4, 32), _node("pve2", 2, 64)]
        scheduler = _make_scheduler(nodes)
        result = scheduler.best_node(method="memory", placement_policy=PlacementPolicy.none)
        assert result == "pve2"  # Most free RAM
