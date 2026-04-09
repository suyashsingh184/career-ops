from __future__ import annotations

from app.models.job import Job
from app.services.people.ranking import rank_contact_hint


def suggested_contacts(job: Job) -> list[dict[str, str | float | None]]:
    suggestions: list[dict[str, str | float | None]] = []
    for contact_type in ("recruiter", "engineering_manager", "team_engineer"):
        confidence, title = rank_contact_hint(job, contact_type)
        query = f'site:linkedin.com/in "{job.company_name}" "{title}"'
        suggestions.append(
            {
                "contact_type": contact_type,
                "name": None,
                "title": title,
                "company": job.company_name,
                "linkedin_url": None,
                "email": None,
                "confidence_score": confidence,
                "search_hint": query,
            }
        )
    return suggestions
