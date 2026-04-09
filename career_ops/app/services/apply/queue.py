from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.exceptions import ApplyPreparationError
from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume
from app.services.ingest.normalize import build_apply_queue_key
from app.services.apply.playwright_runner import build_assisted_apply_plan
from app.types import ApplicationMethod, ApplicationStatus, JobStatus
from app.utils.audit import record_audit_log
from app.utils.dates import utcnow


def queue_application(
    db: Session,
    *,
    job: Job,
    resume: Resume | None,
    method: str,
    explicit_submit_approval: bool = False,
) -> Application:
    notes = None
    status = ApplicationStatus.NOT_STARTED.value
    idempotency_key = build_apply_queue_key(job, method, resume.id if resume else None)
    existing = db.query(Application).filter(Application.idempotency_key == idempotency_key).first()
    if existing is not None:
        return existing
    canonical_job_id = job.canonical_job_id or job.id
    active_statuses = {
        ApplicationStatus.NOT_STARTED.value,
        ApplicationStatus.QUEUED.value,
        ApplicationStatus.PREPARING.value,
        ApplicationStatus.READY_FOR_REVIEW.value,
        ApplicationStatus.SUBMITTED.value,
        ApplicationStatus.CONTACTED.value,
    }
    active_for_canonical = db.scalar(
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .where(((Job.id == canonical_job_id) | (Job.canonical_job_id == canonical_job_id)) & Application.status.in_(active_statuses))
    )
    if active_for_canonical is not None:
        raise ApplyPreparationError("An active application already exists for this canonical job")
    if method == ApplicationMethod.ASSISTED.value:
        plan = build_assisted_apply_plan(job.url, explicit_submit_approval=explicit_submit_approval)
        notes = plan.notes
        status = ApplicationStatus.READY_FOR_REVIEW.value if plan.paused_before_submit else ApplicationStatus.SUBMITTED.value
    elif method == ApplicationMethod.DIRECT_API.value:
        if not explicit_submit_approval:
            raise ApplyPreparationError("Direct API submission requires explicit approval and a known-safe endpoint")
        notes = "Known-safe direct API flow approved."
        status = ApplicationStatus.SUBMITTED.value
    else:
        notes = "Manual apply requested."
        status = ApplicationStatus.QUEUED.value
    application = Application(
        job_id=job.id,
        resume_id=resume.id if resume else None,
        method=method,
        application_url=job.url,
        status=status,
        applied_at=utcnow() if status == ApplicationStatus.SUBMITTED.value else None,
        notes=notes,
        idempotency_key=idempotency_key,
        dry_run=(method != ApplicationMethod.DIRECT_API.value) and not explicit_submit_approval,
        explicit_submit_approved=explicit_submit_approval,
    )
    db.add(application)
    db.flush()
    job.status = JobStatus.READY_TO_APPLY.value if status == ApplicationStatus.READY_FOR_REVIEW.value else job.status
    record_audit_log(
        db,
        entity_type="application",
        entity_id=application.id,
        action="application_queued",
        payload={"idempotency_key": idempotency_key, "method": method, "status": status},
    )
    db.commit()
    db.refresh(application)
    return application
