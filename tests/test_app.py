from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app as api_app
from database import Base, get_db

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, future=True, expire_on_commit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_health_returns_ok():
    api_app.app.dependency_overrides[get_db] = override_get_db
    client = TestClient(api_app.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_returns_answer(monkeypatch):
    api_app.app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        api_app,
        "search_context",
        lambda query, n_results, db: ["Kubernetes manages containers"],
    )
    monkeypatch.setattr(
        api_app,
        "generate_completion",
        lambda prompt: {"response": f"mocked: {prompt[:20]}"},
    )

    client = TestClient(api_app.app)
    response = client.post("/query", json={"q": "What is Kubernetes?", "n_results": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["context_count"] == 1
    assert payload["answer"].startswith("mocked:")


def test_add_requires_api_key_when_configured():
    api_app.app.dependency_overrides[get_db] = override_get_db
    api_app.ADD_API_KEY = "dev-secret"
    client = TestClient(api_app.app)

    unauthorized = client.post("/add", json={"text": "hello"})
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/add",
        json={"text": "hello"},
        headers={"X-API-Key": "dev-secret"},
    )
    assert authorized.status_code == 501
    assert authorized.json()["detail"] == "Use /recipes or /pantry for structured data"
