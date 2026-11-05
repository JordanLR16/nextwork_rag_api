"""Application construction and resource lifecycle; routes live in api/."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import geography, health, pantry, query, recipes
from .config import Settings
from .db.session import Database


def create_app(settings: Settings | None = None, database: Database | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings.from_env()
    database = database if database is not None else Database(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            database.initialize()
            yield
        finally:
            database.dispose()

    application = FastAPI(title="RAG API", lifespan=lifespan)
    application.state.settings = settings
    application.state.database = database
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins), allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )
    for router in (health.router, recipes.router, pantry.router, query.router, geography.router):
        application.include_router(router)
    return application


app = create_app()
