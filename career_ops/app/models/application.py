from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.types import ApplicationMethod, ApplicationStatus


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    resume_id: Mapped[Optional[str]] = mapped_column(ForeignKey("resumes.id"))
    method: Mapped[str] = mapped_column(String(32), default=ApplicationMethod.MANUAL.value)
    application_url: Mapped[Optional[str]] = mapped_column(String(500))
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default=ApplicationStatus.NOT_STARTED.value, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(255), index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    explicit_submit_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text)

    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
