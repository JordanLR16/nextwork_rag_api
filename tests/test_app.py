import app as api_app


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_returns_answer(client, monkeypatch):
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

    response = client.post("/query", json={"q": "What is Kubernetes?", "n_results": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["context_count"] == 1
    assert payload["answer"].startswith("mocked:")


def test_add_requires_api_key_when_configured(client, monkeypatch):
    monkeypatch.setattr(api_app, "ADD_API_KEY", "dev-secret")

    unauthorized = client.post("/add", json={"text": "hello"})
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/add",
        json={"text": "hello"},
        headers={"X-API-Key": "dev-secret"},
    )
    assert authorized.status_code == 501
    assert authorized.json()["detail"] == "Use /recipes or /pantry for structured data"
