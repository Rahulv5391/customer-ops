from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import ticket as ticket_crud
from app.models.agent import SupportAgent
from app.schemas.ticket import (
    TicketBoardChannel,
    TicketBoardColumn,
    TicketCreate,
    TicketDetailResponse,
    TicketEventCreate,
    TicketEventResponse,
    TicketResponse,
    TicketUpdate,
)
from app.services.auth_service import get_current_agent

router = APIRouter(prefix="/tickets", tags=["tickets"])

CHANNELS = ["email", "chat", "phone", "social"]
STATUSES = ["unassigned", "in_progress", "pending_qa", "resolved", "closed"]


@router.get("", response_model=list[TicketResponse])
def list_tickets(
    channel: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    assigned_agent_id: str | None = None,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return ticket_crud.list_tickets(
        db,
        channel=channel,
        status=status,
        priority=priority,
        assigned_agent_id=assigned_agent_id,
    )


@router.get("/board", response_model=list[TicketBoardChannel])
def ticket_board(
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    tickets = ticket_crud.list_tickets(db)
    board = []
    for channel in CHANNELS:
        columns = []
        for status in STATUSES:
            matching = [t for t in tickets if t.channel == channel and t.status == status]
            columns.append(TicketBoardColumn(status=status, tickets=matching))
        board.append(TicketBoardChannel(channel=channel, columns=columns))
    return board


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    ticket = ticket_crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return ticket_crud.create_ticket(db, payload)


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    ticket = ticket_crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket_crud.update_ticket(db, ticket, payload)


@router.post("/{ticket_id}/events", response_model=TicketEventResponse, status_code=201)
def add_ticket_event(
    ticket_id: str,
    payload: TicketEventCreate,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    ticket = ticket_crud.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket_crud.add_ticket_event(db, ticket_id, actor=agent.full_name, data=payload)
