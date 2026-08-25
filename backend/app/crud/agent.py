from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.agent import SupportAgent
from app.schemas.agent import AgentCreate, AgentUpdate


def get_agent(db: Session, agent_id: str) -> SupportAgent | None:
    return db.get(SupportAgent, agent_id)


def get_agent_by_email(db: Session, email: str) -> SupportAgent | None:
    return db.query(SupportAgent).filter(SupportAgent.email == email).first()


def list_agents(
    db: Session, team: str | None = None, on_duty: bool | None = None
) -> list[SupportAgent]:
    q = db.query(SupportAgent)
    if team:
        q = q.filter(SupportAgent.team == team)
    if on_duty is not None:
        q = q.filter(SupportAgent.on_duty == on_duty)
    return q.order_by(SupportAgent.full_name).all()


def create_agent(db: Session, data: AgentCreate) -> SupportAgent:
    payload = data.model_dump(exclude={"password"})
    agent = SupportAgent(**payload, password_hash=hash_password(data.password))
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def update_agent(db: Session, agent: SupportAgent, updates: AgentUpdate) -> SupportAgent:
    for field, value in updates.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return agent


def deactivate_agent(db: Session, agent: SupportAgent) -> SupportAgent:
    """Soft-delete only: tickets/escalations may still reference this agent's
    id (assigned_agent_id is now a real FK), so the row must not disappear."""
    agent.active = False
    agent.on_duty = False
    db.commit()
    db.refresh(agent)
    return agent
