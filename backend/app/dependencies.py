"""HTTP dependencies obtain resources from the current app, never module globals."""

from functools import partial

from fastapi import Depends, Header, HTTPException, Request

from .config import Settings
from .integrations.ollama import generate_completion


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request):
    with request.app.state.database.session_factory() as db:
        yield db


def get_generator(settings: Settings = Depends(get_settings)):
    return partial(generate_completion, settings=settings)


def verify_add_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
):
    if settings.add_api_key and x_api_key != settings.add_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
