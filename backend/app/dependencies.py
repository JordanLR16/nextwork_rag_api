"""HTTP dependencies obtain resources from the current app, never module globals."""

from functools import partial

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClientConnectionError

from .config import Settings
from .integrations.ollama import generate_completion
from .services.users import resolve_user

bearer = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request):
    with request.app.state.database.session_factory() as db:
        yield db


def get_generator(settings: Settings = Depends(get_settings)):
    return partial(generate_completion, settings=settings)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
    db=Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Sign in required", headers={"WWW-Authenticate": "Bearer"})
    if not all((settings.cognito_region, settings.cognito_user_pool_id, settings.cognito_client_id)):
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    try:
        claims = request.app.state.cognito.verify(credentials.credentials)
    except PyJWKClientConnectionError:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"})
    user = resolve_user(db, claims["iss"], claims["sub"])
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return user
