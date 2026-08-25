from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Customer Ops Backend"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite:///./customer_ops.db"

    # LLM / Gemini
    gemini_api_key: str = ""
    gemini_llm_model: str = "gemini-2.0-flash"
    llm_timeout_seconds: float = 8.0
    llm_max_retries: int = 3
    llm_backoff_base_seconds: float = 0.5

    # Circuit breaker (agents/base_agent.py, Phase 3)
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_reset_seconds: float = 30.0

    # If true, agents run in a no-LLM-key fallback mode instead of failing startup
    demo_mode: bool = False

    # RAG (services/rag_service.py, agents/rag_agent.py, Phase 5)
    rag_min_similarity: float = 0.55
    rag_top_k: int = 4

    # Escalation auto-approval (agents/escalation_agent.py, Phase 4)
    auto_approval_threshold_pct: float = 15.0

    # Auth (services/auth_service.py, Phase 2)
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # CORS - explicit origin list used whenever DEBUG is off (see app/main.py)
    cors_origins: list[str] = ["http://localhost:3000"]

    def validate_runtime(self) -> None:
        """Fail fast on missing required secrets rather than degrading silently."""
        if not self.demo_mode and not self.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY must be set unless DEMO_MODE=true."
            )
        if not self.debug and not self.jwt_secret_key:
            raise RuntimeError("JWT_SECRET_KEY must be set when DEBUG=false.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
