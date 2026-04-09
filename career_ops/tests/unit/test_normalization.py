from __future__ import annotations

import pytest

from app.exceptions import NormalizationError
from app.services.ingest.base import IngestedJob
from app.services.ingest.normalize import normalize_job


def test_normalization_removes_boilerplate_and_preserves_core_content() -> None:
    job = IngestedJob(
        source="greenhouse",
        external_id="1",
        company_name="Acme, Inc.",
        title="Backend Engineer",
        location="Remote-Friendly, United States",
        employment_type="Full-time",
        department="Infra",
        posted_at=None,
        url="https://example.com",
        raw_description="""
        <div>Build Python APIs and distributed systems for product teams with strong reliability, observability, and platform ownership responsibilities.</div>
        <p>We are an equal opportunity employer and reasonable accommodations are available.</p>
        """,
    )
    payload = normalize_job(job, allow_stale=True)
    assert "equal opportunity employer" not in payload["normalized_description"]
    assert "Build Python APIs and distributed systems for product teams" in payload["normalized_description"]
    assert payload["normalized_company_name"] == "acme"
    assert payload["normalized_location"] == "remote, us"


def test_normalization_rejects_too_short_descriptions() -> None:
    job = IngestedJob(
        source="greenhouse",
        external_id="1",
        company_name="Acme",
        title="Backend Engineer",
        location="Remote",
        employment_type="Full-time",
        department="Infra",
        posted_at=None,
        url="https://example.com",
        raw_description="<p>short</p>",
    )
    with pytest.raises(NormalizationError):
        normalize_job(job, allow_stale=True)
