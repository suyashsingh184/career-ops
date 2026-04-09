from sqlalchemy import select

from app.models.job import Job
from app.services.ingest.base import IngestedJob
from app.services.ingest.normalize import upsert_jobs


def test_upsert_jobs_deduplicates_by_source_and_external_id(db_session) -> None:
    jobs = [
        IngestedJob(
            source="greenhouse",
            external_id="same",
            company_name="A",
            title="Backend Engineer",
            location="Remote",
            employment_type="Full-time",
            department="Infra",
            posted_at=None,
            url="https://example.com/1",
            raw_description="python api platform infrastructure reliability distributed systems observability" * 2,
        ),
        IngestedJob(
            source="greenhouse",
            external_id="same",
            company_name="A",
            title="Backend Engineer",
            location="Remote",
            employment_type="Full-time",
            department="Infra",
            posted_at=None,
            url="https://example.com/1",
            raw_description="python api updated platform infrastructure reliability distributed systems observability" * 2,
        ),
    ]
    upsert_jobs(db_session, jobs, allow_stale=True)
    assert len(list(db_session.scalars(select(Job)))) == 1
