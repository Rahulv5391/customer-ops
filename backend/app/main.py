from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_runtime()
    Base.metadata.create_all(bind=engine)
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
    return {"status": "ok", "app": settings.app_name}


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
