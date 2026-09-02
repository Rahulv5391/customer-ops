from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, get_db
from app import models  # noqa: F401 - registers all models on Base.metadata
from app.routers import (
    activity_log,
    agents,
    analytics,
    auth,
    chat,
    customers,
    data_sources,
    escalations,
    kb,
    orders,
    tickets,
)
from app.services import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_runtime()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        rag_service.reingest_if_empty(db)
    finally:
        db.close()

    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def health_check():
    """Trivial liveness check - no DB round-trip, safe as Render's own
    configured Health Check Path. Use /health (below) for the fuller
    server+DB readiness check that an external uptime pinger should hit."""
    return {"status": "ok", "app": settings.app_name}


@app.get("/health")
def readiness_check(db: Session = Depends(get_db)):
    """Server + DB readiness. Point an external uptime pinger (e.g.
    cron-job.org, UptimeRobot - both free) at this on a ~10 minute interval:
    it keeps a free Render web service from spinning down after 15 minutes
    idle, AND (since it round-trips the DB) keeps a free-tier Postgres like
    Neon from suspending its compute for the same reason. A ping that only
    hit `/` would keep the web service warm but not the database."""
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={"status": "ok" if db_ok else "degraded", "db": "ok" if db_ok else "unreachable"},
    )


for router_module in (
    auth,
    customers,
    orders,
    tickets,
    agents,
    escalations,
    kb,
    data_sources,
    activity_log,
    chat,
    analytics,
):
    app.include_router(router_module.router, prefix=settings.api_v1_prefix)
