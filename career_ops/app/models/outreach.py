from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.types import OutreachStatus


class OutreachMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outreach_messages"

    contact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("contacts.id"))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    message_type: Mapped[str] = mapped_column(String(32))
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=OutreachStatus.DRAFT.value)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    generation_key: Mapped[str] = mapped_column(String(255), index=True)
    template_version: Mapped[str] = mapped_column(String(32), default="v1")
    version: Mapped[int] = mapped_column(Integer, default=1)
    last_error: Mapped[Optional[str]] = mapped_column(Text)

    contact = relationship("Contact", back_populates="outreach_messages")
    job = relationship("Job", back_populates="outreach_messages")
