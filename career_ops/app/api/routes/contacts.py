from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.contacts import ContactRead
from app.dependencies import get_db
from app.models.contact import Contact
from app.models.job import Job
from app.services.people.finder import suggested_contacts
from app.utils.audit import record_audit_log

router = APIRouter(tags=["contacts"])


@router.post("/jobs/{job_id}/find-contacts", response_model=list[ContactRead])
def find_contacts(job_id: str, db: Session = Depends(get_db)) -> list[Contact]:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = list(db.scalars(select(Contact).where(Contact.job_id == job.id).order_by(Contact.confidence_score.desc())))
    if existing:
        return existing
    contacts: list[Contact] = []
    for payload in suggested_contacts(job):
        contact = Contact(job_id=job.id, **payload)
        db.add(contact)
        db.flush()
        record_audit_log(
            db,
            entity_type="contact",
            entity_id=contact.id,
            action="contact_suggested",
            payload={"search_hint": contact.search_hint, "confidence_score": contact.confidence_score},
        )
        contacts.append(contact)
    db.commit()
    for contact in contacts:
        db.refresh(contact)
    return contacts


@router.get("/jobs/{job_id}/contacts", response_model=list[ContactRead])
def list_contacts(job_id: str, db: Session = Depends(get_db)) -> list[Contact]:
    return list(db.scalars(select(Contact).where(Contact.job_id == job_id).order_by(Contact.confidence_score.desc())))
