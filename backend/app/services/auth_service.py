from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password
from app.crud.agent import get_agent, get_agent_by_email
from app.models.agent import SupportAgent

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def authenticate_agent(db: Session, email: str, password: str) -> SupportAgent | None:
    agent = get_agent_by_email(db, email)
    if not agent or not agent.active:
        return None
    if not verify_password(password, agent.password_hash):
        return None
    return agent


def create_access_token(agent: SupportAgent) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": agent.id,
        "email": agent.email,
        "role": agent.role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_agent(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> SupportAgent:
    credentials_error = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise credentials_error

    agent_id = payload.get("sub")
    if not agent_id:
        raise credentials_error

    agent = get_agent(db, agent_id)
    if not agent or not agent.active:
        raise credentials_error
    return agent


def require_team_lead(agent: SupportAgent = Depends(get_current_agent)) -> SupportAgent:
    if agent.role != "team_lead":
        raise HTTPException(status_code=403, detail="Team lead role required")
    return agent
