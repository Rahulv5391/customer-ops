from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.router_agent import router_agent
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundError
from app.models.agent import SupportAgent
from app.schemas.chat import ActionConfirmRequest, ActionConfirmResponse, ChatRequest, ChatResponse
from app.schemas.customer import CustomerResponse
from app.schemas.escalation import EscalationResponse
from app.schemas.ticket import TicketResponse
from app.services import crm_mutations
from app.services.action_token import decode_action_token
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


@router.post("/action/confirm", response_model=ActionConfirmResponse)
def confirm_action(
    payload: ActionConfirmRequest,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    """Executes a proposed action after confirmation. Only trusts what the
    signed token decodes to, never any other field in the request."""
    try:
        action = decode_action_token(payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    action_type = action["action_type"]
    entity_id = action["entity_id"]
    field_name = action["field_name"]
    field_value = action["field_value"]

    try:
        if action_type == "update_field":
            entity = crm_mutations.update_customer_field(
                db, entity_id, field_name, field_value, actor=agent.full_name
            )
            return ActionConfirmResponse(
                success=True,
                message=f"Updated {field_name}.",
                entity=CustomerResponse.model_validate(entity).model_dump(mode="json"),
            )

        if action_type == "reassign_ticket":
            entity = crm_mutations.reassign_ticket(db, entity_id, field_value, actor=agent.full_name)
            return ActionConfirmResponse(
                success=True,
                message="Ticket reassigned.",
                entity=TicketResponse.model_validate(entity).model_dump(mode="json"),
            )

        if action_type == "schedule_callback":
            entity = crm_mutations.schedule_callback(db, entity_id, field_value, actor=agent.full_name)
            return ActionConfirmResponse(
                success=True,
                message="Callback scheduled.",
                entity=TicketResponse.model_validate(entity).model_dump(mode="json"),
            )

        if action_type == "create_escalation":
            entity = crm_mutations.create_escalation(
                db, action["escalation_payload"] or {}, requested_by=agent.full_name
            )
            return ActionConfirmResponse(
                success=True,
                message="Escalation filed.",
                entity=EscalationResponse.model_validate(entity).model_dump(mode="json"),
            )

        raise HTTPException(status_code=400, detail=f"Unknown action_type '{action_type}'")
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
