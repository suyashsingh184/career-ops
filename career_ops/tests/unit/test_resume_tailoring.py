from app.models.job import Job
from app.services.tailoring.resume_engine import build_tailored_resume


def test_tailored_resume_has_expected_structure(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CAREER_OPS_DATA_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()
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
        status="scored",
        archetype="backend_infra",
    )
    result = build_tailored_resume(job)
    assert result.docx_path.endswith(".docx")
    assert len(result.tailored_experience) >= 3
