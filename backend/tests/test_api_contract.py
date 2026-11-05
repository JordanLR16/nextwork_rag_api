"""Characterize the public API before moving routes and persistence code."""

from unittest.mock import Mock
from uuid import UUID

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db, get_generator


@pytest.fixture
def recipe():
    return {
        "title": "Spinach rice", "author_name": "Chef Zoë",
        "ingredients": ["rice", "spinach", '1 \"pinch\" of salt'],
        "instructions": "Cook rice.\nStir in spinach.",
        "substitutions": ["Use kale instead of spinach"],
        "tagline": "A quick dinner", "description": "One pot, two servings.",
        "tags": ["vegetarian", "weeknight"],
    }


@pytest.mark.parametrize("path,key", [("/recipes", "recipes"), ("/pantry", "items")])
def test_empty_collections(client, path, key):
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"count": 0, key: []}


def test_recipe_round_trip_preserves_all_fields(client, recipe):
    response = client.post("/recipes", json=recipe)
    assert response.status_code == 200
    created = response.json()
    assert created == {"status": "success", "id": str(UUID(created["id"]))}
    listed = client.get("/recipes")
    assert listed.status_code == 200
    assert listed.json() == {"count": 1, "recipes": [{"id": created["id"], **recipe}]}


def test_recipe_optional_fields_have_existing_defaults(client):
    recipe = {"title": "Toast", "author_name": "Cook", "instructions": "Toast bread."}
    response = client.post("/recipes", json=recipe)
    assert response.status_code == 200
    assert client.get("/recipes").json() == {
        "count": 1, "recipes": [{
            "id": response.json()["id"], **recipe, "ingredients": [],
            "substitutions": [], "tags": [], "tagline": None, "description": None,
        }],
    }


@pytest.mark.parametrize("item", [
    {"name": "Rice", "quantity": 2.5, "unit": "cups"},
    {"name": "Salt"},
    {"name": "Eggs", "quantity": 0, "unit": None},
])
def test_pantry_round_trip(client, item):
    response = client.post("/pantry", json=item)
    assert response.status_code == 200
    created = response.json()
    assert created == {"status": "success", "id": str(UUID(created["id"]))}
    listed = client.get("/pantry")
    assert listed.status_code == 200
    assert listed.json() == {"count": 1, "items": [{
        "id": created["id"], "quantity": None, "unit": None, **item,
    }]}


@pytest.mark.parametrize("path,key,payload", [
    ("/recipes", "recipes", {"title": "Toast", "author_name": "Cook", "instructions": "Toast."}),
    ("/pantry", "items", {"name": "Rice"}),
])
def test_repeated_posts_create_distinct_records(client, path, key, payload):
    # Characterizes current behavior: pantry POST inserts, even for an existing name.
    first = client.post(path, json=payload)
    second = client.post(path, json=payload)
    assert first.status_code == second.status_code == 200
    ids = {first.json()["id"], second.json()["id"]}
    assert len(ids) == 2
    listed = client.get(path).json()
    assert listed["count"] == 2
    assert {item["id"] for item in listed[key]} == ids


@pytest.mark.parametrize("field", ["title", "author_name", "instructions"])
@pytest.mark.parametrize("value", [None, ""])
def test_invalid_recipes_are_not_saved(client, recipe, field, value):
    recipe[field] = value
    response = client.post("/recipes", json=recipe)
    assert response.status_code == 422
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])
    assert client.get("/recipes").json()["count"] == 0


@pytest.mark.parametrize("payload,field", [
    ({}, "name"), ({"name": ""}, "name"),
    ({"name": "Rice", "quantity": "many"}, "quantity"),
])
def test_invalid_pantry_items_are_not_saved(client, payload, field):
    response = client.post("/pantry", json=payload)
    assert response.status_code == 422
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])
    assert client.get("/pantry").json()["count"] == 0


@pytest.mark.parametrize("path,payload", [
    ("/recipes", {"title": "Toast", "author_name": "Cook", "instructions": "Toast."}),
    ("/pantry", {"name": "Rice"}),
    ("/add", {"text": "Legacy text"}),
])
@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_write_routes_reject_missing_or_wrong_key(client, monkeypatch, path, payload, headers, application):
    monkeypatch.setattr(application.state.settings, "add_api_key", "test-secret")
    response = client.post(path, json=payload, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert client.get("/recipes").json()["count"] == 0
    assert client.get("/pantry").json()["count"] == 0


@pytest.mark.parametrize("path,payload", [
    ("/recipes", {"title": "Toast", "author_name": "Cook", "instructions": "Toast."}),
    ("/pantry", {"name": "Rice"}),
])
def test_correct_api_key_allows_structured_writes(client, monkeypatch, path, payload, application):
    monkeypatch.setattr(application.state.settings, "add_api_key", "test-secret")
    response = client.post(path, json=payload, headers={"X-API-Key": "test-secret"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_legacy_add_remains_unimplemented_without_auth_configuration(client):
    response = client.post("/add", json={"text": "Something to store"})
    assert response.status_code == 501
    assert response.json() == {"detail": "Use /recipes or /pantry for structured data"}


def test_query_retrieves_saved_recipe_and_pantry_before_generating(client, recipe, monkeypatch, application):
    assert client.post("/recipes", json=recipe).status_code == 200
    assert client.post("/pantry", json={"name": "Rice", "quantity": 2, "unit": "cups"}).status_code == 200
    generate = Mock(return_value={"response": "Cook the spinach rice."})
    application.dependency_overrides[get_generator] = lambda: generate
    response = client.post("/query", json={"q": "How do I make spinach rice?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Cook the spinach rice.", "context_count": 2}
    generate.assert_called_once()
    prompt = generate.call_args.kwargs["prompt"]
    assert "Recipe: Spinach rice" in prompt
    assert recipe["instructions"] in prompt
    assert "Pantry: Rice; quantity: 2.0 cups" in prompt
    assert "Question: How do I make spinach rice?" in prompt


def test_query_limit_applies_to_combined_recipe_and_pantry_context(client, recipe, monkeypatch, application):
    assert client.post("/recipes", json=recipe).status_code == 200
    assert client.post("/pantry", json={"name": "Rice"}).status_code == 200
    generate = Mock(return_value={"response": "Cook rice."})
    application.dependency_overrides[get_generator] = lambda: generate
    response = client.post("/query", json={"q": "rice", "n_results": 1})
    assert response.status_code == 200
    assert response.json()["context_count"] == 1
    prompt = generate.call_args.kwargs["prompt"]
    assert "Recipe: Spinach rice" in prompt
    assert "Pantry:" not in prompt


@pytest.mark.parametrize("question", ["rice", "What can I make?", "%%%"])
def test_query_without_context_skips_model(client, question, generator):
    response = client.post("/query", json={"q": question})
    assert response.status_code == 200
    assert response.json() == {
        "answer": "I do not have enough information to answer that.", "context_count": 0,
    }
    generator.assert_not_called()


@pytest.mark.parametrize("payload,field", [
    ({}, "q"), ({"q": ""}, "q"),
    ({"q": "rice", "n_results": 0}, "n_results"),
    ({"q": "rice", "n_results": 11}, "n_results"),
])
def test_invalid_queries_are_rejected_before_generation(client, payload, field, generator):
    response = client.post("/query", json=payload)
    assert response.status_code == 422
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])
    generator.assert_not_called()


@pytest.mark.parametrize("error,status,detail", [
    (RuntimeError("Model unavailable"), 503, "Model unavailable"),
    (ValueError("private failure detail"), 500, "Internal server error"),
])
def test_query_generation_errors_keep_existing_http_contract(client, recipe, monkeypatch, error, status, detail, application):
    assert client.post("/recipes", json=recipe).status_code == 200
    application.dependency_overrides[get_generator] = lambda: Mock(side_effect=error)
    response = client.post("/query", json={"q": "rice"})
    assert response.status_code == status
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize("method,path,payload,operation", [
    ("GET", "/recipes", None, "execute"),
    ("GET", "/pantry", None, "execute"),
    ("POST", "/recipes", {"title": "Toast", "author_name": "Cook", "instructions": "Toast."}, "commit"),
    ("POST", "/pantry", {"name": "Rice"}, "commit"),
    ("POST", "/query", {"q": "rice"}, "execute"),
])
def test_database_errors_return_generic_500(client, method, path, payload, operation, application):
    failing_db = Mock(spec=Session)
    getattr(failing_db, operation).side_effect = SQLAlchemyError("private database details")

    def override_get_db():
        yield failing_db

    application.dependency_overrides[get_db] = override_get_db
    response = client.request(method, path, **({"json": payload} if payload is not None else {}))
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
