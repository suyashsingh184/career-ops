from pathlib import Path


def test_ingest_score_tailor_flow(client) -> None:
    response = client.post("/jobs/ingest", json={"include_seed": True})
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 3

    job_id = jobs[0]["id"]
    scored = client.post(f"/jobs/{job_id}/score")
    assert scored.status_code == 200
    assert scored.json()["decision"] in {"apply_now", "apply_if_time", "skip"}

    tailored = client.post(f"/jobs/{job_id}/tailor-resume")
    assert tailored.status_code == 200
    assert Path(tailored.json()["docx_path"]).name.endswith(".docx")
