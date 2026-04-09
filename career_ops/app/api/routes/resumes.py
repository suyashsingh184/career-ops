from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas.resumes import ResumeRead
from app.dependencies import get_db
from app.exceptions import ResumeGenerationError
from app.models.job import Job
from app.models.resume import Resume
from app.services.ingest.normalize import build_resume_generation_key
from app.services.tailoring.resume_engine import build_tailored_resume
from app.services.tracker.status_machine import enforce_transition
from app.types import JobStatus
from app.utils.audit import record_audit_log

router = APIRouter(tags=["resumes"])


@router.post("/jobs/{job_id}/tailor-resume", response_model=ResumeRead)
def tailor_resume(job_id: str, db: Session = Depends(get_db)) -> Resume:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    base_resume_name = "backend_distributed_systems"
    generation_key = build_resume_generation_key(job, base_resume_name)
    existing = db.scalar(
        select(Resume)
        .where(Resume.job_id == job.id)
        .where(Resume.generation_key == generation_key)
        .order_by(desc(Resume.version))
    )
    if existing and existing.source_hash == job.hash:
        return existing
    version = (existing.version + 1) if existing else 1
    try:
        payload = build_tailored_resume(job, version=version, base_resume_name=base_resume_name)
    except ResumeGenerationError as exc:
        job.status = JobStatus.FAILED.value
        job.last_error = str(exc)
        record_audit_log(db, entity_type="job", entity_id=job.id, action="resume_generation_failed", payload={"error": str(exc)})
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    resume = Resume(job_id=job.id, **payload.__dict__)
    db.add(resume)
    db.flush()
    enforce_transition(job.status, JobStatus.TAILORED.value, machine="job")
    job.status = JobStatus.TAILORED.value
    record_audit_log(
        db,
        entity_type="resume",
        entity_id=resume.id,
        action="resume_generated",
        payload={"generation_key": resume.generation_key, "version": resume.version},
    )
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/resumes/{resume_id}", response_model=ResumeRead)
def get_resume(resume_id: str, db: Session = Depends(get_db)) -> Resume:
    resume = db.scalar(select(Resume).where(Resume.id == resume_id))
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
