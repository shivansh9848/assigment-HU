from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, projects, runs
from app.api.routers import run_events
from app.api.routers import epics
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.services.seed import seed_admin_if_configured


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)
        seed_admin_if_configured()

    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(projects.router, prefix=settings.api_v1_prefix)
    app.include_router(runs.router, prefix=settings.api_v1_prefix)
    app.include_router(run_events.router, prefix=settings.api_v1_prefix)
    app.include_router(epics.router, prefix=settings.api_v1_prefix)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
