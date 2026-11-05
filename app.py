"""Compatibility entry point; implementation lives in backend.app."""

from backend.app.main import app, create_app

__all__ = ["app", "create_app"]
