from __future__ import annotations

from app.utils.text import most_common_keywords


def extract_keyword_gaps(job_text: str, candidate_text: str, limit: int = 8) -> list[str]:
    job_keywords = most_common_keywords(job_text, limit=30)
    candidate_keywords = set(most_common_keywords(candidate_text, limit=50))
    gaps = [keyword for keyword in job_keywords if keyword not in candidate_keywords]
    return gaps[:limit]
