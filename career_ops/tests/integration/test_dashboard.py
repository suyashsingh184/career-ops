def test_dashboard_and_web_actions(client) -> None:
    ingest = client.post("/jobs/ingest", json={"include_seed": True})
    assert ingest.status_code == 200
    job_id = ingest.json()[0]["id"]

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "Career-Ops" in dashboard.text

    scored = client.post(f"/web/jobs/{job_id}/score", follow_redirects=False)
    assert scored.status_code == 303

    tailored = client.post(f"/web/jobs/{job_id}/tailor", follow_redirects=False)
    assert tailored.status_code == 303

    contacts = client.post(f"/web/jobs/{job_id}/contacts", follow_redirects=False)
    assert contacts.status_code == 303

    outreach = client.post(f"/web/jobs/{job_id}/outreach", follow_redirects=False)
    assert outreach.status_code == 303

    detail = client.get(f"/jobs-view/{job_id}")
    assert detail.status_code == 200
    assert "Outreach Drafts" in detail.text
