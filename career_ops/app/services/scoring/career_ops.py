from __future__ import annotations

from dataclasses import asdict, dataclass

from app.models.job import Job
from app.services.scoring.archetypes import classify_archetype
from app.services.scoring.fit_rules import CandidateProfile, DEFAULT_CANDIDATE
from app.services.scoring.keyword_gap import extract_keyword_gaps


@dataclass
class CareerOpsScore:
    final_score: float
    skill_match: float
    stack_alignment: float
    seniority_fit: float
    domain_fit: float
    location_fit: float
    impact_fit: float
    archetype: str
    keyword_gaps: list[str]
    decision: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _ratio_from_keywords(text: str, keywords: list[str]) -> float:
    lowered = text.lower()
    matches = 0
    for keyword in keywords:
        normalized = keyword.lower()
        variants = {normalized}
        if normalized == "postgresql":
            variants.add("postgres")
        if normalized == "infra":
            variants.add("infrastructure")
        if normalized == "platform engineering":
            variants.add("platform")
        if normalized == "distributed systems":
            variants.add("distributed")
        if any(variant in lowered for variant in variants):
            matches += 1
    if not keywords:
        return 0.0
    return round(min(matches / len(keywords), 1.0) * 10, 2)


def _seniority_score(text: str, candidate: CandidateProfile) -> float:
    lowered = text.lower()
    if candidate.seniority in lowered or "staff" in lowered or "senior" in lowered:
        return 9.0
    if "mid" in lowered:
        return 6.5
    return 7.5


def _location_score(location: str | None, candidate: CandidateProfile, is_remote: bool) -> float:
    if is_remote:
        return 10.0
    lowered = (location or "").lower()
    if any(target in lowered for target in candidate.target_locations):
        return 8.0
    if not lowered:
        return 6.0
    return 4.0


def _archetype_alignment_score(archetype: str) -> float:
    if archetype in {"backend_infra", "platform_engineering", "data_streaming", "fintech_backend", "sre_devops"}:
        return 9.5
    if archetype in {"ai_ml_systems", "fullstack_product"}:
        return 7.0
    return 5.0


def _impact_score(text: str, candidate: CandidateProfile) -> float:
    base = _ratio_from_keywords(text, candidate.impact_keywords)
    lowered = text.lower()
    if sum(term in lowered for term in ["reliability", "platform", "infrastructure", "distributed systems", "kafka"]) >= 2:
        return max(base, 8.0)
    return base


def decision_for_score(score: float) -> str:
    if score >= 8.0:
        return "apply_now"
    if score >= 7.0:
        return "apply_if_time"
    return "skip"


def score_job(job: Job, candidate: CandidateProfile = DEFAULT_CANDIDATE) -> CareerOpsScore:
    combined_text = " ".join(filter(None, [job.title, job.department, job.location, job.normalized_description]))
    archetype = classify_archetype(combined_text)
    skill_match = _ratio_from_keywords(combined_text, candidate.skills)
    stack_alignment = _ratio_from_keywords(combined_text, candidate.preferred_stacks)
    seniority_fit = _seniority_score(combined_text, candidate)
    domain_fit = max(_ratio_from_keywords(combined_text, candidate.domains), _archetype_alignment_score(archetype))
    location_fit = _location_score(job.location, candidate, job.is_remote)
    impact_fit = _impact_score(combined_text, candidate)
    keyword_gaps = extract_keyword_gaps(combined_text, " ".join(candidate.resume_bullets + candidate.skills))
    final_score = round(
        0.30 * skill_match
        + 0.20 * stack_alignment
        + 0.15 * seniority_fit
        + 0.15 * domain_fit
        + 0.10 * location_fit
        + 0.10 * impact_fit,
        2,
    )
    return CareerOpsScore(
        final_score=final_score,
        skill_match=skill_match,
        stack_alignment=stack_alignment,
        seniority_fit=seniority_fit,
        domain_fit=domain_fit,
        location_fit=location_fit,
        impact_fit=impact_fit,
        archetype=archetype,
        keyword_gaps=keyword_gaps,
        decision=decision_for_score(final_score),
    )
