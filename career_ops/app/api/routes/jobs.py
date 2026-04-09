from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.schemas.jobs import JobDecisionRequest, JobRead, JobsIngestRequest
from app.dependencies import get_db
from app.models.company import Company
from app.models.job import Job
from app.exceptions import NormalizationError, ScoringError
from app.services.ingest.ashby import fetch_ashby_jobs
from app.services.ingest.greenhouse import fetch_greenhouse_jobs
from app.services.ingest.normalize import upsert_jobs
from app.services.ingest.lever import fetch_lever_jobs
from app.services.ingest.scraper import scrape_generic_jobs
from app.services.scoring.career_ops import score_job
from app.services.tracker.status_machine import enforce_transition
from app.tasks.ingest_jobs import seed_jobs
from app.types import JobDecision, JobStatus, SourceKind
from app.utils.audit import record_audit_log
from app.utils.retry import CIRCUIT_BREAKERS
from app.utils.dates import within_last_hours

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = logging.getLogger(__name__)


def _resolve_company(db: Session, company_name: str) -> Company:
    company = db.scalar(select(Company).where(Company.name == company_name))
    if company is None:
        company = Company(name=company_name)
        db.add(company)
        db.flush()
    return company


@router.post("/ingest", response_model=list[JobRead])
def ingest_jobs(request: JobsIngestRequest, db: Session = Depends(get_db)) -> list[Job]:
    ingested = []
    failures: list[dict[str, str]] = []
    if request.include_seed or not request.sources:
        ingested.extend(seed_jobs())
    for source in request.sources:
        try:
            record_audit_log(
                db,
                entity_type="source",
                entity_id=source.token or source.company_name or source.kind.value,
                action="ingest_attempt",
                payload={"kind": source.kind.value},
            )
            if source.kind == SourceKind.GREENHOUSE and source.token:
                ingested.extend(fetch_greenhouse_jobs(source.token))
            elif source.kind == SourceKind.LEVER and source.token:
                ingested.extend(fetch_lever_jobs(source.token))
            elif source.kind == SourceKind.ASHBY and source.token:
                ingested.extend(fetch_ashby_jobs(source.token))
            elif source.kind == SourceKind.SCRAPER and source.url and source.company_name:
                ingested.extend(scrape_generic_jobs(source.url, source.company_name))
            elif source.kind != SourceKind.SEED:
                raise HTTPException(status_code=422, detail=f"Missing required source parameters for {source.kind.value}")
        except (httpx.HTTPError, ValueError) as exc:
            logger.exception("Failed to ingest source %s", source.kind.value)
            record_audit_log(
                db,
                entity_type="source",
                entity_id=source.token or source.company_name or source.kind.value,
                action="retry_exhausted",
                payload={"error": str(exc), "circuit_state": CIRCUIT_BREAKERS.snapshot().get(f'{source.kind.value}:{source.token}', {})},
            )
            failures.append({"source": source.kind.value, "error": str(exc)})
            continue
    if request.last_24_hours_only:
        ingested = [job for job in ingested if within_last_hours(job.posted_at, 24)]
    stored = upsert_jobs(db, ingested, allow_stale=request.allow_stale)
    for job in stored:
        company = _resolve_company(db, job.company_name)
        job.company_id = company.id
    if failures:
        record_audit_log(db, entity_type="ingestion", entity_id="batch", action="source_failures", payload={"failures": failures})
    db.commit()
    return stored


@router.get("", response_model=list[JobRead])
def list_jobs(db: Session = Depends(get_db)) -> list[Job]:
    return list(db.scalars(select(Job).order_by(desc(Job.posted_at), desc(Job.created_at))))


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/score", response_model=JobRead)
def score_single_job(job_id: str, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in {JobStatus.NORMALIZED.value, JobStatus.FAILED.value}:
        raise HTTPException(status_code=400, detail="Job must be normalized before scoring")
    try:
        result = score_job(job)
    except Exception as exc:
        job.status = JobStatus.FAILED.value
        job.decision = JobDecision.PENDING_MANUAL_REVIEW.value
        job.last_error = str(exc)
        record_audit_log(db, entity_type="job", entity_id=job.id, action="score_failed", payload={"error": str(exc)})
        db.commit()
        raise HTTPException(status_code=422, detail=f"Scoring failed: {exc}") from exc
    enforce_transition(job.status, JobStatus.SCORED.value, machine="job")
    job.match_score = result.final_score
    job.archetype = result.archetype
    job.decision = result.decision
    job.score_breakdown = result.to_dict()
    job.status = JobStatus.SCORED.value
    record_audit_log(db, entity_type="job", entity_id=job.id, action="score_generated", payload=result.to_dict())
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/decision", response_model=JobRead)
def set_job_decision(job_id: str, request: JobDecisionRequest, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.decision = request.decision.value
    record_audit_log(db, entity_type="job", entity_id=job.id, action="decision", payload=request.model_dump())
    db.commit()
    db.refresh(job)
    return job
