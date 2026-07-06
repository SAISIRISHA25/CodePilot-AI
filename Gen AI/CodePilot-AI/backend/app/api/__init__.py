"""
API package for CodePilot AI.

Exposes the single composed ``api_router`` that ``main.py`` mounts onto
the FastAPI application. Nothing outside this package should import
individual sub-routers (e.g., ``health.router``) directly - always go
through ``api_router`` so the versioned prefix and future middleware
scoped to the API layer stay centralized in one place.
"""

from app.api.router import api_router

__all__ = ["api_router"]