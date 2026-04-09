def test_application_status_update(client) -> None:
    ingest = client.post("/jobs/ingest", json={"include_seed": True})
    job_id = ingest.json()[0]["id"]
    client.post(f"/jobs/{job_id}/score")
    resume = client.post(f"/jobs/{job_id}/tailor-resume").json()
    created = client.post(
        f"/jobs/{job_id}/apply",
        json={"method": "assisted", "resume_id": resume["id"], "explicit_submit_approval": False},
    )
    assert created.status_code == 200
    application_id = created.json()["id"]

    updated = client.post(f"/applications/{application_id}/status", json={"status": "submitted"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "submitted"
