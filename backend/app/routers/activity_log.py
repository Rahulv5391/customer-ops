from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import audit_log as audit_log_crud
from app.models.agent import SupportAgent
from app.schemas.audit_log import ActivityLogResponse
from app.services.auth_service import require_team_lead

# Supervisor tooling, not a general agent screen - matches the original
# PRD's framing of audit-log-style views as part of the admin/supervisor
# view (Architecture.md §6).
router = APIRouter(prefix="/activity-log", tags=["activity-log"])


@router.get("", response_model=list[ActivityLogResponse])
def list_activity(
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _lead: SupportAgent = Depends(require_team_lead),
):
    return audit_log_crud.list_activity(db, entity_type=entity_type, entity_id=entity_id, limit=limit)
