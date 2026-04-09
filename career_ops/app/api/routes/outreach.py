from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas.outreach import OutreachMessageRead
from app.dependencies import get_db
from app.exceptions import OutreachGenerationError
from app.models.contact import Contact
from app.models.job import Job
from app.models.outreach import OutreachMessage
from app.services.outreach.generator import generate_outreach_messages
from app.types import OutreachStatus
from app.utils.audit import record_audit_log

router = APIRouter(tags=["outreach"])


@router.post("/jobs/{job_id}/generate-outreach", response_model=list[OutreachMessageRead])
def generate_outreach(job_id: str, db: Session = Depends(get_db)) -> list[OutreachMessage]:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    contacts = list(db.scalars(select(Contact).where(Contact.job_id == job.id).order_by(Contact.confidence_score.desc())))
    created: list[OutreachMessage] = []
    for payload in generate_outreach_messages(job, contacts):
        existing = db.scalar(
            select(OutreachMessage)
            .where(OutreachMessage.job_id == job.id)
            .where(OutreachMessage.generation_key == payload["generation_key"])
            .order_by(desc(OutreachMessage.version))
        )
        if existing is not None:
            created.append(existing)
            continue
        message = OutreachMessage(job_id=job.id, **payload)
        db.add(message)
        db.flush()
        record_audit_log(
            db,
            entity_type="outreach",
            entity_id=message.id,
            action="outreach_generated",
            payload={"generation_key": message.generation_key, "status": message.status},
        )
        created.append(message)
    db.commit()
    for message in created:
        db.refresh(message)
    return created


@router.get("/jobs/{job_id}/outreach", response_model=list[OutreachMessageRead])
def list_outreach(job_id: str, db: Session = Depends(get_db)) -> list[OutreachMessage]:
    return list(db.scalars(select(OutreachMessage).where(OutreachMessage.job_id == job_id)))
