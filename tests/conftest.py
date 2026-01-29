
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

    from app.main import app
    with TestClient(app) as c:
        yield c
