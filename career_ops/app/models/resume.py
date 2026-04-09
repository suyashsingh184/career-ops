from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, json_type


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    base_resume_name: Mapped[str] = mapped_column(String(255))
    tailored_summary: Mapped[str] = mapped_column(Text)
    tailored_skills: Mapped[str] = mapped_column(Text)
    tailored_experience: Mapped[list[dict[str, str]]] = mapped_column(json_type())
    docx_path: Mapped[str] = mapped_column(String(500))
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    generation_key: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="generated")
    source_hash: Mapped[str] = mapped_column(String(64))
    last_error: Mapped[Optional[str]] = mapped_column(Text)

    job = relationship("Job", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")
