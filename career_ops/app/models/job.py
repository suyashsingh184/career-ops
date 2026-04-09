from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, json_type
from app.types import DuplicateStatus, JobStatus
from app.utils.dates import utcnow


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),)

    source: Mapped[str] = mapped_column(String(50), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    company_id: Mapped[Optional[str]] = mapped_column(ForeignKey("companies.id"))
    company_name: Mapped[str] = mapped_column(String(255), index=True)
    normalized_company_name: Mapped[str] = mapped_column(String(255), index=True, default="")
    title: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    normalized_location: Mapped[str] = mapped_column(String(255), index=True, default="")
    employment_type: Mapped[Optional[str]] = mapped_column(String(100))
    department: Mapped[Optional[str]] = mapped_column(String(255))
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    url: Mapped[str] = mapped_column(String(500))
    raw_description: Mapped[str] = mapped_column(Text)
    normalized_description: Mapped[str] = mapped_column(Text)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer)
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False)
    match_score: Mapped[Optional[float]] = mapped_column(Float)
    archetype: Mapped[Optional[str]] = mapped_column(String(64))
    decision: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default=JobStatus.DISCOVERED.value, index=True)
    hash: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    freshness_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    score_breakdown: Mapped[dict] = mapped_column(json_type(), default=dict)
    canonical_job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.id"))
    duplicate_status: Mapped[str] = mapped_column(String(20), default=DuplicateStatus.CANONICAL.value, index=True)
    duplicate_reason: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)

    company = relationship("Company", back_populates="jobs")
    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="job", cascade="all, delete-orphan")
    outreach_messages = relationship("OutreachMessage", back_populates="job", cascade="all, delete-orphan")
    canonical_job = relationship("Job", remote_side="Job.id")
