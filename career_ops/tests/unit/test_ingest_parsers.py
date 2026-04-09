import json
from pathlib import Path

from app.services.ingest.greenhouse import parse_greenhouse_jobs
from app.services.ingest.lever import parse_lever_jobs


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_parse_real_greenhouse_payload_shape() -> None:
    payload = json.loads((FIXTURES / "greenhouse_anthropic_sample.json").read_text())
    jobs = parse_greenhouse_jobs(payload, board_token="anthropic")
    assert len(jobs) == 1
    assert jobs[0].company_name == "Anthropic"
    assert jobs[0].department == "Software Engineering - Infrastructure"
    assert jobs[0].employment_type == "Full-time"
    assert jobs[0].is_remote is True
    assert jobs[0].posted_at is not None


def test_parse_real_lever_payload_shape() -> None:
    payload = json.loads((FIXTURES / "lever_finch_sample.json").read_text())
    jobs = parse_lever_jobs("finch", payload)
    assert len(jobs) == 1
    assert jobs[0].company_name == "Finch"
    assert jobs[0].employment_type == "Full Time"
    assert jobs[0].is_hybrid is True
    assert jobs[0].salary_min == 125000
    assert jobs[0].currency == "USD"
