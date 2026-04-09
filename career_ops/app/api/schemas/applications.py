from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.types import ApplicationMethod, ApplicationStatus, JobStatus


class ApplicationCreateRequest(BaseModel):
    method: ApplicationMethod = ApplicationMethod.ASSISTED
    resume_id: Optional[str] = None
    explicit_submit_approval: bool = False


class ApplicationStatusUpdateRequest(BaseModel):
    status: ApplicationStatus


class ApplicationRead(BaseModel):
    id: str
    job_id: str
    resume_id: Optional[str]
    method: str
    application_url: Optional[str]
    applied_at: Optional[datetime]
    status: str
    notes: Optional[str]
    idempotency_key: str
    dry_run: bool
    explicit_submit_approved: bool
    last_error: Optional[str]

    model_config = {"from_attributes": True}
