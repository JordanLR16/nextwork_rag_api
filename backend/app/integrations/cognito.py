"""Verify Cognito access tokens locally against a cached, trusted JWKS endpoint."""

import jwt
from jwt import PyJWKClient

from ..config import Settings


class CognitoVerifier:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.keys = PyJWKClient(
            f"{settings.cognito_issuer}/.well-known/jwks.json", timeout=5,
        )

    def verify(self, token: str) -> dict:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256" or not header.get("kid"):
            raise jwt.InvalidTokenError("Invalid signing algorithm or key ID")
        key = self.keys.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token, key.key, algorithms=["RS256"], issuer=self.settings.cognito_issuer,
            # Cognito access tokens identify the client via client_id, not aud.
            options={"verify_aud": False, "require": ["exp", "iat", "iss", "sub", "token_use", "client_id"]},
        )
        if claims["token_use"] != "access" or claims["client_id"] != self.settings.cognito_client_id:
            raise jwt.InvalidTokenError("Not an access token for this application")
        if not isinstance(claims["sub"], str) or not claims["sub"].strip():
            raise jwt.InvalidTokenError("Missing subject")
        return claims
