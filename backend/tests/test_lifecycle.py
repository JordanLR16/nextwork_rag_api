"""Regression checks for the new application and database boundaries."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.db.session import Database
from backend.app.main import create_app
from backend.app.models import PantryItem


def test_factory_does_not_open_database_or_create_files(tmp_path):
    path = tmp_path / "not-created" / "app.db"
    app = create_app(Settings(database_url=f"sqlite:///{path.as_posix()}"))
    assert not path.parent.exists()
    assert "engine" not in app.state.database.__dict__


def test_relative_sqlite_database_stays_in_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    database = Database("sqlite:///./nested/app.db")
    try:
        database.initialize()
        assert (tmp_path / "nested/app.db").is_file()
        with database.session_factory() as session:
            assert session.execute(select(PantryItem)).scalars().all() == []
    finally:
        database.dispose()


def test_app_instances_have_independent_settings_and_databases():
    first = create_app(Settings(database_url="sqlite://", add_api_key="first"))
    second = create_app(Settings(database_url="sqlite://", model_name="another-model"))
    with TestClient(first) as a, TestClient(second) as b:
        assert a.post("/pantry", json={"name": "Rice"}).status_code == 401
        assert a.post("/pantry", json={"name": "Rice"}, headers={"X-API-Key": "first"}).status_code == 200
        assert b.get("/pantry").json() == {"count": 0, "items": []}
        assert b.post("/pantry", json={"name": "Salt"}).status_code == 200
        assert a.get("/health").json()["model"] == "tinyllama"
        assert b.get("/health").json()["model"] == "another-model"
        assert [item["name"] for item in a.get("/pantry").json()["items"]] == ["Rice"]


def test_lifespan_disposes_resources_when_startup_fails():
    database = Mock(spec=Database)
    database.initialize.side_effect = RuntimeError("Cannot initialize")
    app = create_app(Settings(database_url="sqlite://"), database=database)
    with pytest.raises(RuntimeError, match="Cannot initialize"):
        with TestClient(app):
            pass
    database.dispose.assert_called_once()


def test_settings_are_read_per_factory_call(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("MODEL_NAME", "first-model")
    monkeypatch.setenv("CORS_ORIGINS", " https://one.example, ,https://two.example ")
    first = create_app()
    monkeypatch.setenv("MODEL_NAME", "second-model")
    second = create_app()
    assert first.state.settings.model_name == "first-model"
    assert second.state.settings.model_name == "second-model"
    assert first.state.settings.cors_origins == ("https://one.example", "https://two.example")


def test_map_paths_are_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings()
    assert settings.countries_file == PROJECT_ROOT / "data/processed/countries.geojson"
    assert settings.regions_dir == PROJECT_ROOT / "data/processed/regions"
    assert (PROJECT_ROOT / "web/package.json").is_file()
