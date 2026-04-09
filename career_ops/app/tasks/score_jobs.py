from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.models.job import Job
from app.services.scoring.career_ops import score_job
from app.types import JobStatus


def run_score_new_jobs() -> None:
    db = SessionLocal()
    try:
        jobs = list(db.scalars(select(Job).where(Job.status == JobStatus.NORMALIZED.value)))
        for job in jobs:
            result = score_job(job)
            job.match_score = result.final_score
            job.archetype = result.archetype
            job.decision = result.decision
            job.score_breakdown = result.to_dict()
            job.status = JobStatus.SCORED.value
        db.commit()
    finally:
        db.close()
