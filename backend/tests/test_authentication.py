from time import time
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWKClientConnectionError
from sqlalchemy import select

from backend.app.dependencies import get_current_user
from backend.app.integrations.cognito import CognitoVerifier
from backend.app.models import PantryItem, Recipe, User


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def real_auth(client, application, signing_key):
    application.dependency_overrides.pop(get_current_user)
    settings = application.state.settings
    settings.cognito_region = "us-east-1"
    settings.cognito_user_pool_id = "us-east-1_test"
    settings.cognito_client_id = "test-client"
    verifier = CognitoVerifier(settings)
    verifier.keys.get_signing_key_from_jwt = Mock(return_value=SimpleNamespace(key=signing_key.public_key()))
    application.state.cognito = verifier

    def token(subject="alice", **changes):
        claims = {
            "iss": settings.cognito_issuer, "sub": subject, "client_id": "test-client",
            "token_use": "access", "iat": int(time()) - 1, "exp": int(time()) + 300,
            **changes,
        }
        return jwt.encode(claims, signing_key, algorithm="RS256", headers={"kid": "test-key"})

    return token


def headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("method,path,payload", [
    ("GET", "/recipes", None), ("GET", "/pantry", None), ("GET", "/auth/me", None),
    ("POST", "/recipes", {"title": "Rice", "author_name": "Cook", "instructions": "Cook"}),
    ("POST", "/pantry", {"name": "Rice"}), ("POST", "/query", {"q": "rice"}),
    ("POST", "/add", {"text": "rice"}),
])
def test_private_endpoints_require_session(client, real_auth, method, path, payload):
    response = client.request(method, path, json=payload, headers={"X-API-Key": "old-shared-key"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize("changes", [
    {"exp": 1}, {"iss": "https://attacker.example"}, {"client_id": "different-client"},
    {"token_use": "id"}, {"sub": ""}, {"iat": int(time()) + 10000},
])
def test_invalid_claims_are_rejected(client, real_auth, changes):
    assert client.get("/auth/me", headers=headers(real_auth(**changes))).status_code == 401


def test_unsigned_or_tampered_tokens_are_rejected(client, real_auth, signing_key):
    token = real_auth()
    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    tampered = jwt.encode(jwt.decode(token, options={"verify_signature": False}), wrong_key,
                          algorithm="RS256", headers={"kid": "test-key"})
    for invalid in ("malformed", tampered, jwt.encode({"sub": "alice"}, algorithm="none", key=None)):
        assert client.get("/auth/me", headers=headers(invalid)).status_code == 401


def test_jwks_outage_fails_closed(client, application, real_auth):
    application.state.cognito.keys.get_signing_key_from_jwt.side_effect = PyJWKClientConnectionError("offline")
    assert client.get("/auth/me", headers=headers(real_auth())).status_code == 503


def test_unknown_signing_key_is_rejected(client, application, real_auth):
    application.state.cognito.keys.get_signing_key_from_jwt.side_effect = jwt.PyJWKClientError("unknown key")
    assert client.get("/auth/me", headers=headers(real_auth())).status_code == 401


def test_missing_configuration_does_not_allow_access(client, application):
    application.dependency_overrides.pop(get_current_user)
    assert client.get("/recipes").status_code == 401
    assert client.get("/recipes", headers=headers("any-token")).status_code == 503


def test_local_identity_is_stable_and_disabled_users_cannot_access(client, application, real_auth):
    auth = headers(real_auth())
    first = client.get("/auth/me", headers=auth).json()
    assert client.get("/auth/me", headers=auth).json() == first
    with application.state.database.session_factory() as db:
        user = db.get(User, first["id"])
        assert user.subject == "alice"
        user.is_active = False
        db.commit()
    assert client.get("/recipes", headers=auth).status_code == 403


def test_two_users_have_isolated_lists_and_rag_prompts(client, application, generator, real_auth):
    alice, bob = headers(real_auth("alice")), headers(real_auth("bob"))
    bob_id = client.get("/auth/me", headers=bob).json()["id"]
    alice_id = client.get("/auth/me", headers=alice).json()["id"]
    for auth, name in ((alice, "Alice"), (bob, "Bob")):
        recipe = {"title": f"{name} rice", "author_name": name,
                  "instructions": f"{name.lower()}only rice instructions", "owner_id": bob_id}
        assert client.post("/recipes", json=recipe, headers=auth).status_code == 200
        assert client.post("/pantry", json={"name": f"{name} rice", "owner_id": bob_id}, headers=auth).status_code == 200
    assert [r["title"] for r in client.get("/recipes", headers=alice).json()["recipes"]] == ["Alice rice"]
    assert [r["name"] for r in client.get("/pantry", headers=bob).json()["items"]] == ["Bob rice"]
    with application.state.database.session_factory() as db:
        assert db.execute(select(Recipe.owner_id).where(Recipe.title == "Alice rice")).scalar_one() == alice_id
        assert db.execute(select(PantryItem.owner_id).where(PantryItem.name == "Alice rice")).scalar_one() == alice_id
    generator.side_effect = None
    generator.return_value = {"response": "Your recipe"}
    response = client.post("/query", json={"q": "rice", "n_results": 3}, headers=alice)
    assert response.json()["context_count"] == 2
    prompt = generator.call_args.kwargs["prompt"]
    assert "Alice rice" in prompt and "aliceonly" in prompt
    assert "Bob rice" not in prompt and "bobonly" not in prompt
    # Ownership must apply before LIMIT; Bob's alphabetically later recipe still appears.
    response = client.post("/query", json={"q": "rice", "n_results": 1}, headers=bob)
    assert response.json()["context_count"] == 1
    assert "Bob rice" in generator.call_args.kwargs["prompt"]
    generator.reset_mock()
    assert client.post("/query", json={"q": "aliceonly"}, headers=bob).json()["context_count"] == 0
    generator.assert_not_called()
