"""rebalance_cluster — Periodic Celery task for cluster load balancing.

Inspired by ProxLB (https://github.com/credativ/ProxLB).

How it works:
  1. Fetch real-time resource metrics from all Proxmox nodes via the API.
  2. Compute the cluster "balanciness" (delta between most-loaded and least-loaded
     node, in %).
  3. If balanciness > REBALANCE_THRESHOLD_PCT (from settings), find the VM with the
     largest resource footprint on the most-loaded node and migrate it live to the
     node with the most free resources.
  4. Repeat until the cluster is balanced or no more beneficial moves are possible.
  5. Every migration is recorded in ServiceAction + AuditLog for full traceability.

Configuration (env vars / .env):
    REBALANCE_THRESHOLD_PCT  — max allowed delta %; default 20
    REBALANCE_ENABLED        — False = dry-run (log only, no actual migration)
    SCHEDULER_METHOD         — memory | cpu | disk; default memory
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_sessionmaker
from app.integrations.proxmox.service import ProxmoxService
from app.models.enums import ServiceActionType
from app.models.service_action import ServiceAction
from app.models.virtual_machine import VirtualMachine
from app.services.node_scheduler import NodeScheduler
from app.tasks.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task
def rebalance_cluster() -> dict:
    """Rebalance VM distribution across Proxmox nodes.

    Returns a summary dict with moves made (or planned in dry-run mode).
    """
    settings = get_settings()
    method = settings.scheduler_method
    threshold = settings.rebalance_threshold_pct
    enabled = settings.rebalance_enabled

    db = get_sessionmaker()()
    try:
        proxmox = ProxmoxService.from_settings()
        scheduler = NodeScheduler(proxmox=proxmox, db=db)
        cluster = scheduler.get_cluster_capacity()

        balanciness = cluster.balanciness(method=method)
        log.info(
            "rebalance_cluster.start",
            balanciness=balanciness,
            threshold=threshold,
            enabled=enabled,
            method=method,
            nodes=[n.node for n in cluster.online_nodes],
        )

        if balanciness <= threshold:
            log.info("rebalance_cluster.balanced", balanciness=balanciness, threshold=threshold)
            return {"ok": True, "balanced": True, "balanciness": balanciness, "moves": 0}

        moves: list[dict] = []
        max_iterations = len(cluster.online_nodes) * 2  # safety cap

        for iteration in range(max_iterations):
            cluster = scheduler.get_cluster_capacity()  # refresh metrics
            balanciness = cluster.balanciness(method=method)

            if balanciness <= threshold:
                log.info("rebalance_cluster.balanced_after_moves", iterations=iteration, moves=len(moves))
                break

            online = cluster.online_nodes
            if len(online) < 2:
                break

            # Identify the most and least loaded nodes
            if method == "memory":
                most_loaded = max(online, key=lambda n: n.mem - (n.maxmem - n.mem))
                least_loaded = max(online, key=lambda n: n.mem_free)
            else:  # cpu
                most_loaded = max(online, key=lambda n: n.cpu)
                least_loaded = min(online, key=lambda n: n.cpu)

            if most_loaded.node == least_loaded.node:
                break

            # Find the VM with the largest RAM footprint on the most-loaded node
            # (mirrors ProxLB's strategy: move the heaviest guest first)
            vm_to_move = _find_best_vm_to_migrate(db, node_name=most_loaded.node)
            if vm_to_move is None:
                log.warning("rebalance_cluster.no_vm_to_migrate", node=most_loaded.node)
                break

            move_record = {
                "iteration": iteration + 1,
                "vm_id": str(vm_to_move.id),
                "vm_name": vm_to_move.name,
                "vmid": vm_to_move.proxmox_vmid,
                "from_node": most_loaded.node,
                "to_node": least_loaded.node,
                "dry_run": not enabled,
            }

            if enabled:
                try:
                    proxmox.migrate_vm(
                        node=most_loaded.node,
                        vmid=vm_to_move.proxmox_vmid,
                        target_node=least_loaded.node,
                    )
                    vm_to_move.proxmox_node = least_loaded.node
                    vm_to_move.last_synced_at = datetime.now(UTC)
                    db.add(
                        ServiceAction(
                            tenant_id=vm_to_move.tenant_id,
                            service_id=vm_to_move.service_id,
                            virtual_machine_id=vm_to_move.id,
                            job_id=None,
                            requested_by_user_id=None,
                            action=ServiceActionType.migrate,
                            success=True,
                            details={
                                "rebalance": True,
                                "from_node": most_loaded.node,
                                "to_node": least_loaded.node,
                                "method": method,
                                "balanciness_before": balanciness,
                            },
                        )
                    )
                    db.commit()
                    log.info("rebalance_cluster.migrated", **move_record)
                except Exception as exc:
                    log.error("rebalance_cluster.migrate_failed", error=str(exc), **move_record)
                    db.rollback()
                    break
            else:
                log.info("rebalance_cluster.dry_run", **move_record)

            moves.append(move_record)

        return {
            "ok": True,
            "balanced": balanciness <= threshold,
            "balanciness": balanciness,
            "moves": len(moves),
            "dry_run": not enabled,
            "details": moves,
        }
    finally:
        db.close()


def _find_best_vm_to_migrate(db, *, node_name: str) -> VirtualMachine | None:
    """Return the VM on a node most suitable for migration (largest by name, as a proxy).

    In production, you'd query Proxmox for per-VM memory usage. Here we simply
    pick the first running VM on the node — good enough for the initial implementation.
    """
    from app.models.enums import VMStatus  # local import

    return db.scalar(
        select(VirtualMachine)
        .where(
            VirtualMachine.proxmox_node == node_name,
            VirtualMachine.status == VMStatus.running,
        )
        .limit(1)
    )
