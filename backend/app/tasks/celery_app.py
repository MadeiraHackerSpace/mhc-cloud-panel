from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

always_eager = os.getenv("CELERY_ALWAYS_EAGER", "false").lower() in {"1", "true", "yes"}
broker_url = "memory://" if always_eager else settings.redis_url
backend_url = "cache+memory://" if always_eager else settings.redis_url

celery_app = Celery(
    "mhc_cloud_panel",
    broker=broker_url,
    backend=backend_url,
    include=[
        "app.tasks.provision_vm",
        "app.tasks.sync_vm_status",
        "app.tasks.billing",
        "app.tasks.rebalance_cluster",
        "app.tasks.maintenance_drain",
    ],
)

celery_app.conf.update(
    task_default_queue="default",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=always_eager,
    task_eager_propagates=True,
    # ── Celery Beat periodic schedule ──────────────────────────────────────
    # Sync VM status from Proxmox every 5 minutes
    # Check overdue invoices and suspend services every hour
    # Rebalance cluster every 30 minutes (dry-run by default; enable via REBALANCE_ENABLED=true)
    beat_schedule={
        "sync-vm-status-every-5min": {
            "task": "app.tasks.sync_vm_status.sync_vm_status",
            "schedule": crontab(minute="*/5"),
        },
        "mark-overdue-and-suspend-hourly": {
            "task": "app.tasks.billing.mark_overdue_and_suspend",
            "schedule": crontab(minute=0),  # top of every hour
            "kwargs": {"grace_days": 3},
        },
        "rebalance-cluster-every-30min": {
            "task": "app.tasks.rebalance_cluster.rebalance_cluster",
            "schedule": crontab(minute="*/30"),
        },
    },
)
