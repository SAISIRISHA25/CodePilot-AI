"""
FastAPI application entrypoint and factory.

This module is the single composition root for the HTTP interface layer:
it wires together configuration, logging, middleware, exception
handlers, and the API router into one runnable FastAPI application.

Design decision:
    An application *factory* (``create_app``) is used instead of a bare
    module-level ``app = FastAPI()`` so that:
        1. Tests can call ``create_app()`` repeatedly to get a fresh,
           isolated application instance per test module.
        2. Future deployment variants (e.g., a worker process with a
           different middleware stack) can reuse the same factory with
           different arguments if needed.
    A module-level ``app`` instance is still exposed at the bottom of
    this file, since ASGI servers (uvicorn/gunicorn) need a concrete
    importable object to serve.
"""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.version import get_version
from app.exceptions.handlers import register_exception_handlers
from app.middleware.request_logger import RequestIDLoggingMiddleware
from app.persistence.database import initialize_database
from app.dependencies import get_workflow_factory, get_workflow_executor

logger = logging.getLogger("codepilot.main")


def _configure_logging() -> None:
    """Configure root logging with StreamHandler and FileHandler."""
    settings = get_settings()
    log_format = (
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        if not settings.logging.json_format
        else '{"time": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": "%(message)s"}'
    )
    
    # Configure root logger levels and handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.logging.level.upper())
    
    # Clear existing handlers to prevent duplicate formatting on reload
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    # Console stream handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)
    
    # File handler writing to data/codepilot.log
    try:
        os.makedirs("data", exist_ok=True)
        file_handler = logging.FileHandler("data/codepilot.log", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown behavior.

    Startup and shutdown logic is centralized here rather than spread
    across ``@app.on_event`` decorators (deprecated in modern FastAPI).
    This is also the designated seam for future resource initialization
    - e.g., warming a ChromaDB client or opening a SQLite connection
    pool - without needing to modify route handlers.

    Args:
        app: The FastAPI application instance this lifespan is bound to.

    Yields:
        None: Control returns to FastAPI to serve requests between
        startup and shutdown.
    """
    settings = get_settings()
    logger.info(
        "application.startup",
        extra={
            "app_name": settings.app.name,
            "environment": settings.app.environment.value,
            "version": get_version(),
        },
    )

    initialize_database()
    app.state.workflow_factory = get_workflow_factory()
    app.state.workflow_executor = get_workflow_executor()

    yield

    logger.info("application.shutdown", extra={"app_name": settings.app.name})

    # NOTE: Future modules will release/close resources initialized
    # above (e.g., closing DB connections) here, after the yield.


def create_app() -> FastAPI:
    """Construct and configure the CodePilot AI FastAPI application.

    Wires together, in order:
        1. Logging configuration.
        2. The FastAPI instance itself (with lifespan and metadata).
        3. CORS middleware.
        4. Request correlation ID / structured logging middleware.
        5. Global exception handlers.
        6. The composed API router.

    Returns:
        FastAPI: A fully configured, ready-to-serve application instance.
    """
    _configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app.name,
        version=get_version(),
        description=(
            "CodePilot AI - Enterprise Multi-Agent Software Engineering "
            "Copilot. Workflow-driven API for SDLC document ingestion and "
            "AI-agent-generated engineering artifacts."
        ),
        lifespan=lifespan,
    )

    # --------------------------------------------------------------------
    # CORS configuration
    # --------------------------------------------------------------------
    # NOTE: Origins are intentionally permissive ("*") for local capstone
    # development against the Vite dev server. In a real production
    # deployment this MUST be restricted to the actual frontend origin(s)
    # (e.g., via a dedicated settings field), since wildcard origins
    # combined with credentials are a well-known security risk.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request correlation ID + structured request logging. Added after
    # CORS so that even CORS-preflight-adjacent requests are still
    # observable; order matters because Starlette applies middleware in
    # reverse registration order around the request.
    app.add_middleware(RequestIDLoggingMiddleware)

    # Global exception handlers - the single translation point from
    # internal exceptions to client-facing error responses.
    register_exception_handlers(app)

    # Mount the versioned API router (see app/api/router.py).
    app.include_router(api_router)

    return app


# Module-level application instance for ASGI servers, e.g.:
#   uvicorn app.main:app --reload
app = create_app()