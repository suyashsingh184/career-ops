from __future__ import annotations

from app.services.ingest.base import IngestedJob
from app.services.ingest.normalize import upsert_jobs


def test_fuzzy_duplicates_map_to_canonical_job(db_session) -> None:
    jobs = [
        IngestedJob(
            source="greenhouse",
            external_id="g-1",
            company_name="Acme Inc",
            title="Senior Backend Engineer",
            location="Remote",
            employment_type="Full-time",
            department="Platform",
            posted_at=None,
            url="https://example.com/1",
            raw_description="Build Python services, distributed systems, and platform infrastructure for product teams." * 2,
        ),
        IngestedJob(
            source="lever",
            external_id="l-1",
            company_name="Acme",
            title="Senior Backend Engineer",
            location="Remote",
            employment_type="Full-time",
            department="Platform",
            posted_at=None,
            url="https://example.com/2",
            raw_description="Build Python services, distributed systems, and platform infrastructure for product teams." * 2,
        ),
    ]
    stored = upsert_jobs(db_session, jobs, allow_stale=True)
    canonical = next(job for job in stored if job.duplicate_status == "canonical")
    duplicate = next(job for job in stored if job.duplicate_status == "duplicate")
    assert duplicate.canonical_job_id == canonical.id
