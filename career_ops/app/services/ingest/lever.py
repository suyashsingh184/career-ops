from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.exceptions import SourceFetchError
from app.services.ingest.base import IngestedJob
from app.utils.retry import RATE_LIMITER, run_with_retry
from app.utils.text import collapse_whitespace


def _salary_range(post: dict[str, Any]) -> tuple[Optional[int], Optional[int], Optional[str]]:
    salary_range = post.get("salaryRange") or {}
    return salary_range.get("min"), salary_range.get("max"), salary_range.get("currency")


def parse_lever_jobs(company: str, payload: list[dict[str, Any]]) -> list[IngestedJob]:
    jobs: list[IngestedJob] = []
    for post in payload:
        categories = post.get("categories", {})
        salary_min, salary_max, currency = _salary_range(post)
        location = categories.get("location")
        if not location:
            all_locations = categories.get("allLocations") or []
            location = collapse_whitespace(", ".join(str(item) for item in all_locations))
        workplace_type = str(post.get("workplaceType") or "").lower()
        jobs.append(
            IngestedJob(
                source="lever",
                external_id=post["id"],
                company_name=company.replace("-", " ").title(),
                title=post["text"],
                location=location,
                employment_type=categories.get("commitment"),
                department=categories.get("team"),
                posted_at=datetime.fromtimestamp(post["createdAt"] / 1000),
                url=post["hostedUrl"],
                raw_description=post.get("descriptionPlain")
                or post.get("descriptionBodyPlain")
                or post.get("description", ""),
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency,
                is_remote="remote" in str(location or "").lower() or workplace_type == "remote",
                is_hybrid=workplace_type == "hybrid",
            )
        )
    return jobs


def fetch_lever_jobs(company: str) -> list[IngestedJob]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    settings = get_settings()

    def _fetch() -> list[dict[str, Any]]:
        RATE_LIMITER.wait("lever", settings.source_rate_limit_per_sec)
        response = httpx.get(
            url,
            timeout=settings.source_timeout_seconds,
            headers={"User-Agent": f"{settings.app_name} ingestion bot"},
        )
        if response.status_code in {401, 403, 404}:
            raise ValueError(f"Lever board returned non-retryable status {response.status_code}")
        try:
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise SourceFetchError(str(exc)) from exc

    payload = run_with_retry(_fetch, source_key=f"lever:{company}")
    return parse_lever_jobs(company, payload)
