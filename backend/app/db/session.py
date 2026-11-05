"""App-owned, lazy database resources shared by HTTP and command-line entry points."""

import time
from functools import cached_property
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .base import Base


class Database:
    def __init__(self, url: str):
        self.url = url

    @cached_property
    def engine(self):
        url = make_url(self.url)
        options = {}
        if url.get_backend_name() == "sqlite":
            options["connect_args"] = {"check_same_thread": False}
            if url.database in (None, "", ":memory:"):
                options["poolclass"] = StaticPool
            else:
                # Parse the URL instead of stripping sqlite://, which turned
                # relative paths into drive-root paths on Windows.
                Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(url, future=True, echo=False, **options)

    @cached_property
    def session_factory(self):
        return sessionmaker(
            bind=self.engine, autoflush=False, future=True, expire_on_commit=False,
        )

    def wait_for_db(self, max_retries: int = 15, delay: float = 2.0):
        for attempt in range(1, max_retries + 1):
            try:
                with self.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                return
            except OperationalError:
                if attempt == max_retries:
                    raise
                time.sleep(delay)

    def initialize(self):
        # Register every model before creating tables. Existing deployments still
        # use the SQL migration for column changes; create_all is not a migrator.
        from .. import models  # noqa: F401

        self.wait_for_db()
        Base.metadata.create_all(bind=self.engine)

    def dispose(self):
        if "engine" in self.__dict__:
            self.engine.dispose()
