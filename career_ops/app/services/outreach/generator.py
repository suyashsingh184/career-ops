from __future__ import annotations

from jinja2 import Template

from app.services.ingest.normalize import build_outreach_generation_key
from app.models.contact import Contact
from app.models.job import Job
from app.services.outreach.templates import FOLLOW_UP_TEMPLATE, MANAGER_TEMPLATE, RECRUITER_TEMPLATE
from app.types import OutreachStatus


def _archetype_phrase(archetype: str | None) -> str:
    return (archetype or "backend infrastructure").replace("_", " ")


def generate_outreach_messages(job: Job, contacts: list[Contact], *, template_version: str = "v1") -> list[dict[str, str | int | None]]:
    messages: list[dict[str, str | int | None]] = []
    templates = {
        "recruiter_message": RECRUITER_TEMPLATE,
        "hiring_manager_message": MANAGER_TEMPLATE,
        "follow_up_message": FOLLOW_UP_TEMPLATE,
    }
    primary_contact = contacts[0] if contacts else None
    context = {
        "contact_name": primary_contact.name if primary_contact and primary_contact.name else "there",
        "company_name": job.company_name,
        "job_title": job.title,
        "job_focus": job.department or _archetype_phrase(job.archetype),
        "archetype_phrase": _archetype_phrase(job.archetype),
    }
    for message_type, raw_template in templates.items():
        body = Template(raw_template).render(**context).strip()
        contact_type = "recruiter" if "recruiter" in message_type else "engineering_manager"
        messages.append(
            {
                "contact_id": primary_contact.id if primary_contact else None,
                "message_type": message_type,
                "subject": f"{job.title} at {job.company_name}",
                "body": body,
                "status": OutreachStatus.DRAFT.value,
                "generation_key": build_outreach_generation_key(job, contact_type, template_version),
                "template_version": template_version,
                "version": 1,
                "last_error": None,
            }
        )
    return messages
