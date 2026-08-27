from sqlalchemy.orm import Session

from app.core.observability import get_logger
from app.crud.audit_log import record_activity as _insert_activity
from app.schemas.audit_log import ActivityLogCreate

logger = get_logger("audit_service")


def record_activity(
    db: Session, actor: str, action_type: str, entity_type: str, entity_id: str, summary: str
) -> None:
    """Best-effort audit trail write. Failures here are logged, not raised."""
    try:
        _insert_activity(
            db,
            ActivityLogCreate(
                action_type=action_type,
                actor=actor,
                entity_type=entity_type,
                entity_id=entity_id,
                summary=summary,
            ),
        )
    except Exception as exc:
        db.rollback()
        logger.warning(f"Failed to record activity log: {exc}")
