from backend.app.services import query as query_service


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "sqlite", "model": "tinyllama"}


def test_query_returns_answer(client, generator, monkeypatch):
    monkeypatch.setattr(
        query_service, "search_context",
        lambda query, n_results, db: ["Rice cooks in water."],
    )
    generator.side_effect = lambda prompt: {"response": f"mocked: {prompt[:20]}"}
    response = client.post("/query", json={"q": "How do I cook rice?", "n_results": 3})
    assert response.status_code == 200
    assert response.json()["context_count"] == 1
    assert response.json()["answer"].startswith("mocked:")


def test_add_requires_api_key_when_configured(client, application, monkeypatch):
    monkeypatch.setattr(application.state.settings, "add_api_key", "dev-secret")
    unauthorized = client.post("/add", json={"text": "hello"})
    assert unauthorized.status_code == 401
    authorized = client.post(
        "/add", json={"text": "hello"}, headers={"X-API-Key": "dev-secret"},
    )
    assert authorized.status_code == 501
    assert authorized.json()["detail"] == "Use /recipes or /pantry for structured data"
