from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.applications import ApplicationCreateRequest, ApplicationRead, ApplicationStatusUpdateRequest
from app.dependencies import get_db
from app.exceptions import ApplyPreparationError
from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume
from app.services.apply.queue import queue_application
from app.services.tracker.status_machine import enforce_transition
from app.types import ApplicationStatus, JobStatus
from app.utils.audit import record_audit_log

router = APIRouter(tags=["applications"])


@router.post("/jobs/{job_id}/apply", response_model=ApplicationRead)
def apply_to_job(job_id: str, request: ApplicationCreateRequest, db: Session = Depends(get_db)) -> Application:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    resume = db.get(Resume, request.resume_id) if request.resume_id else None
    try:
        application = queue_application(
            db,
            job=job,
            resume=resume,
            method=request.method.value,
            explicit_submit_approval=request.explicit_submit_approval,
        )
    except ApplyPreparationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return application


@router.get("/applications", response_model=list[ApplicationRead])
def list_applications(db: Session = Depends(get_db)) -> list[Application]:
    return list(db.scalars(select(Application).order_by(Application.created_at.desc())))


@router.post("/applications/{application_id}/status", response_model=ApplicationRead)
def update_application_status(
    application_id: str,
    request: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db),
) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    previous_status = application.status
    try:
        enforce_transition(application.status, request.status.value, machine="application")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    application.status = request.status.value
    if application.job is not None and request.status.value == ApplicationStatus.SUBMITTED.value:
        application.job.status = JobStatus.APPLIED.value
    record_audit_log(
        db,
        entity_type="application",
        entity_id=application.id,
        action="state_transition",
        payload={"from": previous_status, "to": request.status.value},
    )
    db.commit()
    db.refresh(application)
    return application
