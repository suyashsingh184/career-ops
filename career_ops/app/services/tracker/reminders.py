from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application


def pending_follow_ups(db: Session) -> list[Application]:
    return list(db.scalars(select(Application).where(Application.status.in_(["applied", "contacted"]))))
