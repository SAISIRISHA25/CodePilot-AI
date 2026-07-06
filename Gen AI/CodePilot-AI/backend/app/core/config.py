"""
Application configuration accessor.

This module exposes exactly one public function, ``get_settings()``,
which is the sole, sanctioned way for the rest of the application to
obtain configuration. No other module should construct ``Settings()``
directly — routing every consumer through this single accessor gives us
one seam for caching, testing overrides, and future secret-manager
integration (e.g., swapping ``.env`` for AWS Secrets Manager later
without touching a single call site elsewhere in the app).

Design decision:
    ``functools.lru_cache`` is used instead of a plain module-level
    global instance for two reasons:
        1. It defers construction until first use (lazy loading),
           avoiding import-order side effects.
        2. Tests can call ``get_settings.cache_clear()`` to force
           re-reading environment variables between test cases,
           which a plain global would make awkward.
"""

from functools import lru_cache

from app.core.settings import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached, composed application settings instance.

    The underlying ``Settings`` object is constructed once per process
    (cached via ``lru_cache``) and reused on every subsequent call,
    avoiding repeated ``.env`` file parsing on every access.

    Returns:
        Settings: The fully composed, validated application settings.

    Example:
        >>> from app.core.config import get_settings
        >>> settings = get_settings()
        >>> settings.app.name
        'CodePilot AI'
    """
    return Settings()