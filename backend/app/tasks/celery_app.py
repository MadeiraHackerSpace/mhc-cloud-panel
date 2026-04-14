from __future__ import annotations

import os

from celery import Celery

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
)
