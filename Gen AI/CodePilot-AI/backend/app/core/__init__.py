"""
Core package for CodePilot AI.

Contains cross-cutting technical concerns that do not belong to any
single Clean Architecture layer: configuration loading, application
constants, and version metadata.

This package must remain free of business logic. It exists to be
depended upon by every other layer (domain, application, infrastructure,
interface), never the other way around.

Public API:
    get_settings: Cached accessor for composed application settings.
    __version__: Current semantic version of the backend.
"""

from app.core.config import get_settings
from app.core.version import __version__

__all__ = ["get_settings", "__version__"]