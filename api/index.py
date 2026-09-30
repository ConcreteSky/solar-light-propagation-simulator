"""Vercel ASGI entrypoint for the existing FastAPI application."""

from backend.app.main import app

__all__ = ["app"]
