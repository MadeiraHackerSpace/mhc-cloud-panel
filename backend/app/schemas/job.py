from __future__ import annotations

import uuid
from datetime import datetime

from app.models.enums import JobStatus
from app.schemas.common import APIModel


class JobOut(APIModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    service_id: uuid.UUID | None
    requested_by_user_id: uuid.UUID | None
    job_key: str
    job_type: str
    status: JobStatus
    celery_task_id: str | None
    payload: dict
    result: dict
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
