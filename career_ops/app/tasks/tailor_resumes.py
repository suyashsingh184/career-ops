from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.models.job import Job
from app.models.resume import Resume
from app.services.ingest.normalize import build_resume_generation_key
from app.services.tailoring.resume_engine import build_tailored_resume
from app.types import JobStatus


def run_tailor_resumes() -> None:
    db = SessionLocal()
    try:
        jobs = list(db.scalars(select(Job).where(Job.decision.in_(["apply_now", "apply_if_time"]))))
        for job in jobs:
            generation_key = build_resume_generation_key(job, "backend_distributed_systems")
            if db.scalar(select(Resume).where(Resume.generation_key == generation_key).where(Resume.source_hash == job.hash)):
                continue
            latest = db.scalar(select(Resume).where(Resume.generation_key == generation_key).order_by(Resume.version.desc()))
            payload = build_tailored_resume(job, version=(latest.version + 1) if latest else 1)
            db.add(Resume(job_id=job.id, **payload.__dict__))
            job.status = JobStatus.TAILORED.value
        db.commit()
    finally:
        db.close()
