from __future__ import annotations

import app.api.routes.jobs as jobs_routes


def test_source_failure_does_not_break_seed_ingestion(client, monkeypatch) -> None:
    monkeypatch.setattr(jobs_routes, "fetch_greenhouse_jobs", lambda _: (_ for _ in ()).throw(ValueError("boom")))
    response = client.post(
        "/jobs/ingest",
        json={
            "include_seed": True,
            "allow_stale": True,
            "sources": [{"kind": "greenhouse", "token": "definitely-invalid-board-token"}],
        },
    )
    assert response.status_code == 200
    assert len(response.json()) == 3
