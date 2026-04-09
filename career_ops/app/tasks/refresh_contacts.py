from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.models.contact import Contact
from app.models.job import Job
from app.services.people.finder import suggested_contacts


def run_refresh_contacts() -> None:
    db = SessionLocal()
    try:
        jobs = list(db.scalars(select(Job).where(Job.decision.in_(["apply_now", "apply_if_time"]))))
        for job in jobs:
            if db.scalar(select(Contact).where(Contact.job_id == job.id)) is not None:
                continue
            for payload in suggested_contacts(job):
                db.add(Contact(job_id=job.id, **payload))
        db.commit()
    finally:
        db.close()
