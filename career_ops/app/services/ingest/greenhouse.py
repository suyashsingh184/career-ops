from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.exceptions import SourceFetchError
from app.services.ingest.base import IngestedJob
from app.utils.retry import RATE_LIMITER, run_with_retry
from app.utils.text import collapse_whitespace


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _metadata_map(post: dict[str, Any]) -> dict[str, Any]:
    return {
        str(item.get("name", "")).lower(): item.get("value")
        for item in post.get("metadata", [])
        if item.get("name")
    }


def _department_name(post: dict[str, Any]) -> Optional[str]:
    departments = post.get("departments") or []
    if departments:
        return collapse_whitespace(", ".join(str(item.get("name", "")).strip() for item in departments if item.get("name")))
    return None


def parse_greenhouse_jobs(payload: dict[str, Any], board_token: Optional[str] = None) -> list[IngestedJob]:
    jobs: list[IngestedJob] = []
    for post in payload.get("jobs", []):
        metadata = _metadata_map(post)
        location_name = (post.get("location") or {}).get("name")
        company_name = (
            post.get("company_name")
            or payload.get("company")
            or payload.get("meta", {}).get("board_name")
            or board_token
            or "Unknown Company"
        )
        location_type = str(metadata.get("location type") or "").lower()
        jobs.append(
            IngestedJob(
                source="greenhouse",
                external_id=str(post["id"]),
                company_name=company_name,
                title=post["title"],
                location=location_name,
                employment_type=metadata.get("employment type"),
                department=_department_name(post),
                posted_at=_parse_datetime(post.get("updated_at") or post.get("first_published")),
                url=post["absolute_url"],
                raw_description=post.get("content", ""),
                is_remote="remote" in str(location_name or "").lower() or "remote" in location_type,
                is_hybrid="hybrid" in str(location_name or "").lower() or "hybrid" in location_type,
            )
        )
    return jobs


def fetch_greenhouse_jobs(board_token: str) -> list[IngestedJob]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    settings = get_settings()

    def _fetch() -> dict[str, Any]:
        RATE_LIMITER.wait("greenhouse", settings.source_rate_limit_per_sec)
        response = httpx.get(
            url,
            timeout=settings.source_timeout_seconds,
            headers={"User-Agent": f"{settings.app_name} ingestion bot"},
        )
        if response.status_code in {401, 403, 404}:
            raise ValueError(f"Greenhouse board returned non-retryable status {response.status_code}")
        try:
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise SourceFetchError(str(exc)) from exc

    payload = run_with_retry(_fetch, source_key=f"greenhouse:{board_token}")
    return parse_greenhouse_jobs(payload, board_token=board_token)
