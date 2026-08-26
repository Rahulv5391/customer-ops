from pydantic import BaseModel

from app.schemas.agent import AgentResponse


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agent: AgentResponse
