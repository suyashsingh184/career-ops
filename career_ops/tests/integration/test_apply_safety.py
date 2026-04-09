from __future__ import annotations


def test_assisted_apply_defaults_to_dry_run_review(client) -> None:
    ingest = client.post("/jobs/ingest", json={"include_seed": True, "allow_stale": True})
    job_id = ingest.json()[0]["id"]
    client.post(f"/jobs/{job_id}/score")
    resume = client.post(f"/jobs/{job_id}/tailor-resume").json()
    response = client.post(f"/jobs/{job_id}/apply", json={"method": "assisted", "resume_id": resume["id"]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert payload["status"] == "ready_for_review"
