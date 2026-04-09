from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime settings loaded from environment variables."""

    app_name: str = "Career-Ops"
    env: str = "local"
    database_url: str = "sqlite:///./career_ops.db"
    base_url: str = "http://127.0.0.1:8000"
    secret_key: str = Field(default="change-me", repr=False)
    data_dir: Path = Path("./data")
    log_level: str = "INFO"
    scheduler_timezone: str = "America/Los_Angeles"
    recent_job_hours: int = 24
    enable_scheduler: bool = True
    freshness_hours: int = 24
    retry_max_attempts: int = 3
    retry_backoff_base: float = 1.0
    retry_jitter: float = 0.25
    source_rate_limit_per_sec: float = 1.0
    source_timeout_seconds: int = 10
    max_concurrent_per_source: int = 2
    circuit_breaker_threshold: int = 5
    circuit_breaker_window_minutes: int = 10
    circuit_breaker_cooldown_minutes: int = 15
    allow_auto_submit: bool = False
    playwright_dry_run_default: bool = True
    min_job_description_length: int = 80

    @property
    def resume_dir(self) -> Path:
        return self.data_dir / "resumes"

    @property
    def outreach_dir(self) -> Path:
        return self.data_dir / "outreach"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env = os.environ
    return Settings(
        app_name=env.get("CAREER_OPS_APP_NAME", "Career-Ops"),
        env=env.get("CAREER_OPS_ENV", "local"),
        database_url=env.get("CAREER_OPS_DATABASE_URL", "sqlite:///./career_ops.db"),
        base_url=env.get("CAREER_OPS_BASE_URL", "http://127.0.0.1:8000"),
        secret_key=env.get("CAREER_OPS_SECRET_KEY", "change-me"),
        data_dir=Path(env.get("CAREER_OPS_DATA_DIR", "./data")),
        log_level=env.get("CAREER_OPS_LOG_LEVEL", "INFO"),
        scheduler_timezone=env.get("CAREER_OPS_SCHEDULER_TIMEZONE", "America/Los_Angeles"),
        recent_job_hours=int(env.get("CAREER_OPS_RECENT_JOB_HOURS", "24")),
        enable_scheduler=env.get("CAREER_OPS_ENABLE_SCHEDULER", "true").lower() in {"1", "true", "yes", "on"},
        freshness_hours=int(env.get("CAREER_OPS_FRESHNESS_HOURS", "24")),
        retry_max_attempts=int(env.get("CAREER_OPS_RETRY_MAX_ATTEMPTS", "3")),
        retry_backoff_base=float(env.get("CAREER_OPS_RETRY_BACKOFF_BASE", "1.0")),
        retry_jitter=float(env.get("CAREER_OPS_RETRY_JITTER", "0.25")),
        source_rate_limit_per_sec=float(env.get("CAREER_OPS_SOURCE_RATE_LIMIT_PER_SEC", "1.0")),
        source_timeout_seconds=int(env.get("CAREER_OPS_SOURCE_TIMEOUT_SECONDS", "10")),
        max_concurrent_per_source=int(env.get("CAREER_OPS_MAX_CONCURRENT_PER_SOURCE", "2")),
        circuit_breaker_threshold=int(env.get("CAREER_OPS_CIRCUIT_BREAKER_THRESHOLD", "5")),
        circuit_breaker_window_minutes=int(env.get("CAREER_OPS_CIRCUIT_BREAKER_WINDOW_MINUTES", "10")),
        circuit_breaker_cooldown_minutes=int(env.get("CAREER_OPS_CIRCUIT_BREAKER_COOLDOWN_MINUTES", "15")),
        allow_auto_submit=env.get("CAREER_OPS_ALLOW_AUTO_SUBMIT", "false").lower() in {"1", "true", "yes", "on"},
        playwright_dry_run_default=env.get("CAREER_OPS_PLAYWRIGHT_DRY_RUN_DEFAULT", "true").lower()
        in {"1", "true", "yes", "on"},
        min_job_description_length=int(env.get("CAREER_OPS_MIN_JOB_DESCRIPTION_LENGTH", "80")),
    )
