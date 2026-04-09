from __future__ import annotations

from datetime import datetime

import httpx

from app.services.ingest.base import IngestedJob


def parse_ashby_jobs(company: str, payload: dict) -> list[IngestedJob]:
    jobs: list[IngestedJob] = []
    for post in payload.get("jobs", []):
        jobs.append(
            IngestedJob(
                source="ashby",
                external_id=post["id"],
                company_name=company,
                title=post["title"],
                location=post.get("location"),
                employment_type=post.get("employmentType"),
                department=post.get("departmentName"),
                posted_at=datetime.fromisoformat(post["publishedAt"].replace("Z", "+00:00"))
                if post.get("publishedAt")
                else None,
                url=post["jobUrl"],
                raw_description=post.get("descriptionHtml", ""),
                is_remote=bool(post.get("isRemote")),
                is_hybrid="hybrid" in (post.get("location", "").lower()),
            )
        )
    return jobs


def fetch_ashby_jobs(company_slug: str) -> list[IngestedJob]:
    url = f"https://jobs.ashbyhq.com/api/non-user-graphql?company={company_slug}"
    payload = httpx.post(
        url,
        json={"query": "{ jobBoard { jobs { id title location employmentType departmentName publishedAt jobUrl descriptionHtml isRemote } } }"},
        timeout=30,
    ).json()
    return parse_ashby_jobs(company_slug, {"jobs": payload.get("data", {}).get("jobBoard", {}).get("jobs", [])})
