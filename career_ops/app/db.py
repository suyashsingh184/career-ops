from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, MetaData, create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import get_settings
from app.utils.dates import utcnow

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class Base(DeclarativeBase):
    metadata = metadata


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UUIDPrimaryKeyMixin:
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))


def json_type() -> type[JSON]:
    return JSON().with_variant(JSONB, "postgresql")


settings = get_settings()
connect_args: dict[str, Any] = {}
engine_kwargs: dict[str, Any] = {"future": True, "connect_args": connect_args}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if settings.database_url in {"sqlite://", "sqlite:///:memory:"}:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def ensure_runtime_dirs() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    for child in ("raw_jobs", "processed_jobs", "resumes", "outreach", "logs", ".pycache"):
        (Path(settings.data_dir) / child).mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    from app import models  # noqa: F401

    ensure_runtime_dirs()
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
