from backend.app.services import query as query_service


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "sqlite", "model": "tinyllama"}


def test_query_returns_answer(client, generator, monkeypatch):
    monkeypatch.setattr(
        query_service, "search_context",
        lambda query, n_results, db, owner_id: ["Rice cooks in water."],
    )
    generator.side_effect = lambda prompt: {"response": f"mocked: {prompt[:20]}"}
    response = client.post("/query", json={"q": "How do I cook rice?", "n_results": 3})
    assert response.status_code == 200
    assert response.json()["context_count"] == 1
    assert response.json()["answer"].startswith("mocked:")


def test_add_requires_login(client, application):
    from backend.app.dependencies import get_current_user

    authenticated = application.dependency_overrides.pop(get_current_user)
    unauthorized = client.post("/add", json={"text": "hello"})
    assert unauthorized.status_code == 401
    application.dependency_overrides[get_current_user] = authenticated
    authorized = client.post(
        "/add", json={"text": "hello"},
    )
    assert authorized.status_code == 501
    assert authorized.json()["detail"] == "Use /recipes or /pantry for structured data"
