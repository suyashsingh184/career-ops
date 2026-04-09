from __future__ import annotations

from app.models.job import Job


def rank_contact_hint(job: Job, contact_type: str) -> tuple[float, str]:
    base_scores = {"recruiter": 0.91, "engineering_manager": 0.84, "team_engineer": 0.78}
    title_map = {
        "recruiter": f"Recruiter for {job.title}",
        "engineering_manager": f"Engineering Manager, {job.department or job.title}",
        "team_engineer": f"Senior Engineer on {job.department or 'relevant'} team",
    }
    return base_scores[contact_type], title_map[contact_type]
