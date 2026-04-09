from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.exceptions import ResumeGenerationError
from app.models.job import Job
from app.services.ingest.normalize import build_resume_generation_key
from app.services.tailoring.bullet_library import BULLET_LIBRARY
from app.services.tailoring.exporter import export_docx
from app.services.tailoring.skills_templates import SKILLS_BY_ARCHETYPE
from app.services.tailoring.summary_templates import SUMMARY_TEMPLATES
from app.utils.files import safe_slug
from app.utils.retry import run_with_retry
from app.utils.dates import utcnow


@dataclass
class TailoredResumePayload:
    base_resume_name: str
    tailored_summary: str
    tailored_skills: str
    tailored_experience: list[dict[str, str]]
    docx_path: str
    generation_key: str
    version: int
    status: str
    source_hash: str
    pdf_path: Optional[str] = None
    last_error: Optional[str] = None


def build_tailored_resume(job: Job, *, version: int = 1, base_resume_name: str = "backend_distributed_systems") -> TailoredResumePayload:
    archetype = job.archetype or "backend_infra"
    summary = SUMMARY_TEMPLATES[archetype]
    prioritized = [
        bullet for bullet in BULLET_LIBRARY if any(word in bullet.lower() for word in job.normalized_description.lower().split()[:20])
    ]
    chosen = (prioritized + BULLET_LIBRARY)[:4]
    experience = [{"headline": job.title, "bullet": bullet} for bullet in chosen]
    skills = ", ".join(SKILLS_BY_ARCHETYPE[archetype])
    settings = get_settings()
    generation_key = build_resume_generation_key(job, base_resume_name)
    timestamp = utcnow().strftime("%Y%m%d%H%M%S")
    output_name = f"{safe_slug(job.company_name)}_{safe_slug(job.title)}_{job.id}_{timestamp}_v{version}.docx"
    docx_path = settings.resume_dir / output_name
    try:
        run_with_retry(
            lambda: export_docx(docx_path, title=f"{job.title} Resume", summary=summary, skills=skills, experience=experience),
            source_key=f"resume:{job.id}",
        )
    except Exception as exc:  # pragma: no cover - exercised in retry/file tests
        raise ResumeGenerationError(str(exc)) from exc
    return TailoredResumePayload(
        base_resume_name=base_resume_name,
        tailored_summary=summary,
        tailored_skills=skills,
        tailored_experience=experience,
        docx_path=str(docx_path),
        generation_key=generation_key,
        version=version,
        status="generated",
        source_hash=job.hash,
    )
