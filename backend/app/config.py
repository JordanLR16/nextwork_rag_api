"""Explicit application settings; environment is read when building an app."""

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORS_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


@dataclass
class Settings:
    database_url: str = "sqlite:///./db/app.db"
    model_name: str = "tinyllama"
    ollama_host: str = ""
    add_api_key: str = ""
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    countries_file: Path = PROJECT_ROOT / "data/processed/countries.geojson"
    regions_dir: Path = PROJECT_ROOT / "data/processed/regions"

    @property
    def database_backend(self) -> str:
        return "postgres" if self.database_url.startswith("postgres") else "sqlite"

    @classmethod
    def from_env(cls):
        origins = os.getenv("CORS_ORIGINS", "")
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///./db/app.db"),
            model_name=os.getenv("MODEL_NAME", "tinyllama"),
            ollama_host=os.getenv("OLLAMA_HOST", "").strip(),
            add_api_key=os.getenv("ADD_API_KEY", "").strip(),
            cors_origins=tuple(value.strip() for value in origins.split(",") if value.strip())
            if origins.strip() else DEFAULT_CORS_ORIGINS,
        )
