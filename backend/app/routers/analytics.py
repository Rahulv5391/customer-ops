from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent import SupportAgent
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    CountResponse,
    TicketVolumePoint,
    TopIssueCategory,
)
from app.services import analytics_service
from app.services.auth_service import get_current_agent

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def summary(
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return analytics_service.get_summary(db)


@router.get("/ticket-volume", response_model=list[TicketVolumePoint])
def ticket_volume(
    days: int = 7,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return analytics_service.ticket_volume_by_day(db, days=days)


@router.get("/top-issue-categories", response_model=list[TopIssueCategory])
def top_issue_categories(
    limit: int = 5,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return analytics_service.top_issue_category(db, limit=limit)


@router.get("/escalations-pending", response_model=CountResponse)
def escalations_pending(
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return CountResponse(count=analytics_service.pending_escalations_count(db))


@router.get("/tickets-resolved-today", response_model=CountResponse)
def tickets_resolved_today(
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return CountResponse(count=analytics_service.tickets_resolved_today(db))
