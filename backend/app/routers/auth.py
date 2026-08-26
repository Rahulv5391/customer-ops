from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent import SupportAgent
from app.schemas.agent import AgentResponse
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import authenticate_agent, create_access_token, get_current_agent

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    agent = authenticate_agent(db, payload.email, payload.password)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(agent)
    return LoginResponse(access_token=token, agent=AgentResponse.model_validate(agent))


@router.get("/me", response_model=AgentResponse)
def me(current_agent: SupportAgent = Depends(get_current_agent)):
    return current_agent
