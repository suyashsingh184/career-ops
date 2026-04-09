from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.services.ingest.base import IngestedJob
from app.services.ingest.normalize import upsert_jobs


def seed_jobs() -> list[IngestedJob]:
    fixture_path = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "sample_jobs.json"
    payload = json.loads(fixture_path.read_text())
    jobs: list[IngestedJob] = []
    for item in payload:
        if item.get("posted_at"):
            item["posted_at"] = datetime.fromisoformat(item["posted_at"])
        jobs.append(IngestedJob(**item))
    return jobs


def run_ingest_job_sources() -> None:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    db: Session = SessionLocal()
    try:
        upsert_jobs(db, seed_jobs())
    finally:
        db.close()
