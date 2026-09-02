from sqlalchemy.orm import Session

from app.models.audit_log import ActivityLog
from app.schemas.audit_log import ActivityLogCreate


def record_activity(db: Session, data: ActivityLogCreate) -> ActivityLog:
    entry = ActivityLog(**data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_activity(
    db: Session,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ActivityLog]:
    q = db.query(ActivityLog)
    if entity_type:
        q = q.filter(ActivityLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(ActivityLog.entity_id == entity_id)
    return q.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit).all()
