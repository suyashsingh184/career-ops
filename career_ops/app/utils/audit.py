from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_log(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    payload: dict,
    actor: str = "system",
) -> AuditLog:
    log = AuditLog(entity_type=entity_type, entity_id=entity_id, action=action, payload=payload, actor=actor)
    db.add(log)
    return log
