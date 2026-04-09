from app.models.job import Job
from app.services.scoring.career_ops import decision_for_score, score_job


def test_scoring_produces_apply_now_for_strong_backend_match() -> None:
    job = Job(
        source="greenhouse",
        external_id="1",
        company_name="ScaleForge",
        title="Senior Backend Engineer",
        location="Remote",
        employment_type="Full-time",
        department="Infrastructure",
        url="https://example.com",
        raw_description="Python Postgres Kafka distributed systems platform engineering reliability",
        normalized_description="Python Postgres Kafka distributed systems platform engineering reliability",
        is_remote=True,
        is_hybrid=False,
        hash="abc",
        status="discovered",
    )
    result = score_job(job)
    assert result.final_score >= 8.0
    assert result.decision == "apply_now"
    assert decision_for_score(6.9) == "skip"
