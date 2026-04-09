from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Contact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contacts"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    contact_type: Mapped[str] = mapped_column(String(32))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    search_hint: Mapped[Optional[str]] = mapped_column(Text)

    job = relationship("Job", back_populates="contacts")
    outreach_messages = relationship("OutreachMessage", back_populates="contact")
