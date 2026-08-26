from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import agent as agent_crud
from app.models.agent import SupportAgent
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from app.services.auth_service import get_current_agent, require_team_lead

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
def list_agents(
    team: str | None = None,
    on_duty: bool | None = None,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return agent_crud.list_agents(db, team=team, on_duty=on_duty)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    agent = agent_crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
    _lead: SupportAgent = Depends(require_team_lead),
):
    return agent_crud.create_agent(db, payload)


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    db: Session = Depends(get_db),
    _lead: SupportAgent = Depends(require_team_lead),
):
    agent = agent_crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_crud.update_agent(db, agent, payload)


@router.delete("/{agent_id}", response_model=AgentResponse)
def deactivate_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    _lead: SupportAgent = Depends(require_team_lead),
):
    agent = agent_crud.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_crud.deactivate_agent(db, agent)
