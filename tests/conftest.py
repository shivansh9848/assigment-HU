
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.base import Base

@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    storage_root = tmp_path / "storage"

    test_settings = Settings(
        DATABASE_URL=f"sqlite:///{db_path}",
        STORAGE_ROOT=storage_root,
        JWT_SECRET="test-secret",
        MAX_UPLOAD_MB=1,
        TAVILY_API_KEY="test-tavily-key",
        SEED_ADMIN_EMAIL="admin@example.com",
        SEED_ADMIN_PASSWORD="adminpass",
    )

    from app.core import config as config_module
    config_module.get_settings.cache_clear()
    monkeypatch.setattr(config_module, "get_settings", lambda: test_settings)

    engine = create_engine(test_settings.database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    from app.db import session as session_module
    session_module.engine = engine
    session_module.SessionLocal = TestingSessionLocal

    # Some modules import SessionLocal directly; patch them too so they use the test DB.
    from app.api.routers import runs as runs_router
    runs_router.SessionLocal = TestingSessionLocal

    from app.api.routers import ws as ws_router
    ws_router.SessionLocal = TestingSessionLocal

    from app.services import seed as seed_service
    seed_service.SessionLocal = TestingSessionLocal

    from app.main import app

    # Avoid real network calls in Milestone 2 research jobs.
    from app.services import research as research_module
    from app.api.routers import runs as runs_router

    def _fake_tavily_search(*, api_key: str, query: str, max_results: int = 8, search_depth: str = "basic", include_answer: str | bool = "basic", timeout_seconds: float = 30.0):
        return research_module.ResearchResult(
            query=query,
            answer=f"Fake answer for: {query}",
            results=[
                research_module.TavilyResult(
                    title="Example",
                    url="https://example.com",
                    content="Example content",
                    score=0.9,
                )
            ],
        )

    monkeypatch.setattr(research_module, "tavily_search", _fake_tavily_search)
    monkeypatch.setattr(runs_router, "tavily_search", _fake_tavily_search)

    with TestClient(app) as c:
        yield c
