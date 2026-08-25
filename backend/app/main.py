from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401 - registers all models on Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_runtime()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

# Never combine a wildcard origin with allow_credentials=True (invalid per the
# CORS spec, and a bug in the MedAssist AI reference this project fixes - see
# Architecture.md §8.7). Wildcard is only used in DEBUG, without credentials.
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
