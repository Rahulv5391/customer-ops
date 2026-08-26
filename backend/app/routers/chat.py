from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.router_agent import router_agent
from app.core.database import get_db
from app.models.agent import SupportAgent
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.auth_service import get_current_agent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    message = await router_agent.route_message(
        db=db,
        message=payload.message,
        agent_name=agent.full_name,
        role=agent.role,
        active_entity_id=payload.active_entity_id,
        active_entity_type=payload.active_entity_type,
    )
    return ChatResponse(messages=[message])
