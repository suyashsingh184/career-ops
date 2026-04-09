from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.models.contact import Contact
from app.models.job import Job
from app.models.outreach import OutreachMessage
from app.services.outreach.generator import generate_outreach_messages
from app.services.people.finder import suggested_contacts


def run_generate_outreach_for_ready_jobs() -> None:
    db = SessionLocal()
    try:
        jobs = list(db.scalars(select(Job).where(Job.decision.in_(["apply_now", "apply_if_time"]))))
        for job in jobs:
            contacts = list(db.scalars(select(Contact).where(Contact.job_id == job.id)))
            if not contacts:
                for payload in suggested_contacts(job):
                    db.add(Contact(job_id=job.id, **payload))
                db.flush()
                contacts = list(db.scalars(select(Contact).where(Contact.job_id == job.id)))
            for payload in generate_outreach_messages(job, contacts):
                if db.scalar(select(OutreachMessage).where(OutreachMessage.generation_key == payload["generation_key"])):
                    continue
                db.add(OutreachMessage(job_id=job.id, **payload))
        db.commit()
    finally:
        db.close()
