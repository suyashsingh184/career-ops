from __future__ import annotations


def test_idempotent_tailoring_and_outreach(client) -> None:
    ingest = client.post("/jobs/ingest", json={"include_seed": True, "allow_stale": True})
    job_id = ingest.json()[0]["id"]
    client.post(f"/jobs/{job_id}/score")

    resume_one = client.post(f"/jobs/{job_id}/tailor-resume")
    resume_two = client.post(f"/jobs/{job_id}/tailor-resume")
    assert resume_one.status_code == 200
    assert resume_two.status_code == 200
    assert resume_one.json()["id"] == resume_two.json()["id"]

    client.post(f"/jobs/{job_id}/find-contacts")
    outreach_one = client.post(f"/jobs/{job_id}/generate-outreach")
    outreach_two = client.post(f"/jobs/{job_id}/generate-outreach")
    assert len(outreach_one.json()) == len(outreach_two.json()) == 3
    assert outreach_one.json()[0]["id"] == outreach_two.json()[0]["id"]
