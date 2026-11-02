"""Isolated API fixtures; no local database or running Ollama is required."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# database.py creates an engine at import time. Isolate that too, before any
# application import, regardless of the developer's DATABASE_URL environment.
with patch.dict("os.environ", {"DATABASE_URL": "sqlite://"}):
    import app as api_app
    from database import Base, get_db


@pytest.fixture(autouse=True)
def isolate_app_state(monkeypatch):
    previous_overrides = api_app.app.dependency_overrides.copy()
    api_app.app.dependency_overrides.clear()
    monkeypatch.setattr(api_app, "ADD_API_KEY", "")
    # Fail visibly if a test accidentally reaches the real model integration.
    monkeypatch.setattr(
        api_app, "generate_completion",
        Mock(side_effect=AssertionError("Test must mock model generation")),
    )
    try:
        yield
    finally:
        api_app.app.dependency_overrides.clear()
        api_app.app.dependency_overrides.update(previous_overrides)


@pytest.fixture
def client(monkeypatch):
    # StaticPool shares the same in-memory database with TestClient's thread.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        with sessions() as db:
            yield db

    api_app.app.dependency_overrides[get_db] = override_get_db
    # The fixture initializes its own schema; startup must not touch the local DB.
    monkeypatch.setattr(api_app, "wait_for_db", lambda: None)
    monkeypatch.setattr(api_app, "init_db", lambda: None)
    try:
        with TestClient(api_app.app) as test_client:
            yield test_client
    finally:
        engine.dispose()
