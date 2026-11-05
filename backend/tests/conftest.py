"""Each test gets its own app, database, settings, and fake model generator."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.dependencies import get_generator
from backend.app.main import create_app


@pytest.fixture
def generator():
    return Mock(side_effect=AssertionError("Test must configure model generation"))


@pytest.fixture
def application(generator, tmp_path):
    settings = Settings(
        database_url="sqlite://", countries_file=tmp_path / "countries.geojson",
        regions_dir=tmp_path / "regions",
    )
    app = create_app(settings)
    app.dependency_overrides[get_generator] = lambda: generator
    return app


@pytest.fixture
def client(application):
    # Exercise the real startup/schema/shutdown lifecycle against an in-memory DB.
    with TestClient(application) as test_client:
        yield test_client
