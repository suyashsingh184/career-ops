def test_outreach_generation_flow(client) -> None:
    response = client.post("/jobs/ingest", json={"include_seed": True})
    job_id = response.json()[0]["id"]
    client.post(f"/jobs/{job_id}/score")
    contacts = client.post(f"/jobs/{job_id}/find-contacts")
    assert contacts.status_code == 200
    assert len(contacts.json()) == 3

    outreach = client.post(f"/jobs/{job_id}/generate-outreach")
    assert outreach.status_code == 200
    assert len(outreach.json()) == 3
