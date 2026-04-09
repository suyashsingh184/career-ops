from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import NormalizationError
from app.models.job import Job
from app.services.ingest.base import IngestedJob
from app.types import DuplicateStatus, JobStatus
from app.utils.audit import record_audit_log
from app.utils.dates import within_last_hours
from app.utils.hashing import stable_hash
from app.utils.text import (
    normalize_company_name,
    normalize_description,
    normalize_location,
    similarity,
)


def _posted_day_bucket(posted_at: datetime | None) -> str:
    if posted_at is None:
        return "unknown"
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    return posted_at.date().isoformat()


def _validate_normalized_description(description: str) -> None:
    settings = get_settings()
    if not description or len(description) < settings.min_job_description_length:
        raise NormalizationError("Job description is empty or too short after normalization")


def _normalize_salary(value: int | None) -> int | None:
    if value is None:
        return None
    return value if value > 0 else None


def build_job_idempotency_key(job: IngestedJob) -> str:
    return stable_hash(job.source, job.external_id, str(job.posted_at or "unknown"))


def build_resume_generation_key(job: Job, base_resume_name: str) -> str:
    return stable_hash(job.id, base_resume_name, job.hash, job.archetype or "unknown")


def build_outreach_generation_key(job: Job, contact_type: str, template_version: str) -> str:
    return stable_hash(job.id, contact_type, template_version)


def build_apply_queue_key(job: Job, application_mode: str, resume_id: str | None) -> str:
    return stable_hash(job.id, application_mode, resume_id or "no-resume")


def normalize_job(job: IngestedJob, *, allow_stale: bool = False) -> dict[str, object]:
    normalized_description = normalize_description(job.raw_description)
    _validate_normalized_description(normalized_description)
    normalized_company = normalize_company_name(job.company_name)
    normalized_location_value = normalize_location(job.location)
    freshness_valid = within_last_hours(job.posted_at, get_settings().freshness_hours)
    if not freshness_valid and not allow_stale:
        raise NormalizationError("Job is older than the configured freshness window")
    return {
        "source": job.source,
        "external_id": job.external_id,
        "company_name": job.company_name,
        "normalized_company_name": normalized_company,
        "title": job.title.strip(),
        "location": job.location,
        "normalized_location": normalized_location_value,
        "employment_type": job.employment_type,
        "department": job.department,
        "posted_at": job.posted_at,
        "url": job.url,
        "raw_description": job.raw_description,
        "normalized_description": normalized_description,
        "salary_min": _normalize_salary(job.salary_min),
        "salary_max": _normalize_salary(job.salary_max),
        "currency": (job.currency or "").upper() or None,
        "is_remote": job.is_remote or "remote" in normalized_location_value,
        "is_hybrid": job.is_hybrid or "hybrid" in normalized_location_value,
        "hash": stable_hash(
            normalized_company,
            job.title.strip().lower(),
            normalized_location_value,
            normalized_description,
            _posted_day_bucket(job.posted_at),
        ),
        "idempotency_key": build_job_idempotency_key(job),
        "freshness_valid": freshness_valid,
        "status": JobStatus.NORMALIZED.value,
    }


def _find_exact_or_hash_match(db: Session, source: str, external_id: str, content_hash: str) -> Job | None:
    existing = db.scalar(select(Job).where((Job.source == source) & (Job.external_id == external_id)))
    if existing is not None:
        return existing
    return db.scalar(select(Job).where(Job.hash == content_hash))


def _find_fuzzy_duplicate(db: Session, payload: dict[str, object]) -> Job | None:
    candidates = list(
        db.scalars(
            select(Job).where(Job.normalized_company_name == payload["normalized_company_name"]).where(Job.id != payload.get("id"))
        )
    )
    title = str(payload["title"])
    normalized_description = str(payload["normalized_description"])
    normalized_location_value = str(payload["normalized_location"])
    for candidate in candidates:
        title_similarity = similarity(title, candidate.title)
        description_similarity = similarity(normalized_description[:1200], candidate.normalized_description[:1200])
        location_match = normalized_location_value == candidate.normalized_location or bool(
            payload["is_remote"] and candidate.is_remote
        )
        if title_similarity >= 0.87 and description_similarity >= 0.92 and location_match:
            return candidate
    return None


def _apply_duplicate_markers(job: Job, canonical: Job, reason: str) -> None:
    job.canonical_job_id = canonical.id
    job.duplicate_status = DuplicateStatus.DUPLICATE.value
    job.duplicate_reason = reason
    job.status = JobStatus.DUPLICATE.value


def upsert_jobs(
    db: Session,
    jobs: list[IngestedJob],
    *,
    allow_stale: bool = False,
    actor: str = "system",
) -> list[Job]:
    stored: list[Job] = []
    seen_by_identity: dict[tuple[str, str], Job] = {}
    for source_job in jobs:
        try:
            payload = normalize_job(source_job, allow_stale=allow_stale)
        except NormalizationError as exc:
            record_audit_log(
                db,
                entity_type="job_source",
                entity_id=f"{source_job.source}:{source_job.external_id}",
                action="normalization_failed",
                payload={"error": str(exc)},
                actor=actor,
            )
            continue

        identity = (str(payload["source"]), str(payload["external_id"]))
        existing = seen_by_identity.get(identity) or _find_exact_or_hash_match(
            db, str(payload["source"]), str(payload["external_id"]), str(payload["hash"])
        )
        if existing is None:
            existing = _find_fuzzy_duplicate(db, payload)
        if existing is not None:
            if existing.source == payload["source"] and existing.external_id == payload["external_id"]:
                for key, value in payload.items():
                    setattr(existing, key, value)
                existing.status = JobStatus.NORMALIZED.value
                record_audit_log(
                    db,
                    entity_type="job",
                    entity_id=existing.id,
                    action="ingest_upsert",
                    payload={"idempotency_key": existing.idempotency_key},
                    actor=actor,
                )
                stored.append(existing)
                seen_by_identity[identity] = existing
                continue

            created = Job(**payload)
            _apply_duplicate_markers(created, existing.canonical_job or existing, "fuzzy_duplicate" if existing.source != payload["source"] else "content_hash")
            db.add(created)
            db.flush()
            record_audit_log(
                db,
                entity_type="job",
                entity_id=created.id,
                action="dedup_decision",
                payload={"canonical_job_id": created.canonical_job_id, "reason": created.duplicate_reason},
                actor=actor,
            )
            stored.append(created)
            seen_by_identity[identity] = created
            continue

        created = Job(**payload)
        created.duplicate_status = DuplicateStatus.CANONICAL.value
        db.add(created)
        db.flush()
        record_audit_log(
            db,
            entity_type="job",
            entity_id=created.id,
            action="ingest_upsert",
            payload={"idempotency_key": created.idempotency_key},
            actor=actor,
        )
        stored.append(created)
        seen_by_identity[identity] = created
    db.commit()
    for item in stored:
        db.refresh(item)
    return stored
