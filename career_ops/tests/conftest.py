from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_ROOT = Path(__file__).resolve().parents[1]
os.environ["CAREER_OPS_DATABASE_URL"] = "sqlite://"
os.environ["CAREER_OPS_DATA_DIR"] = str((TEST_ROOT / "data").resolve())
os.environ["CAREER_OPS_ENABLE_SCHEDULER"] = "false"

from app.db import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
