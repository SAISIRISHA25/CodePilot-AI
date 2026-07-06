"""
Top-level API router and standard response envelope.

This module defines:
    1. ``APIResponse`` - the standard success response envelope used by
       every endpoint in the application, so clients always receive a
       predictable shape (``success``, ``data``, ``message``).
    2. ``api_router`` - the single aggregator router that composes every
       resource-specific sub-router (health, and later: projects,
       documents, pipeline-runs, artifacts) under one versioned prefix.

Design decision:
    Routers are aggregated here rather than included directly on the
    FastAPI ``app`` instance in ``main.py``. This keeps ``main.py``
    focused purely on application wiring (middleware, exception
    handlers, lifespan) and gives the API surface its own composition
    root that can be unit-tested independently of the full app.
"""

from typing import Generic, TypeVar

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.constants import API_V1_PREFIX

# Generic type parameter for the payload carried inside an APIResponse.
DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard success response envelope for every API endpoint.

    Attributes:
        success: Always ``True`` for successful responses. Mirrors the
            ``success`` flag on ``app.exceptions.handlers.ErrorResponse``
            so clients can branch on one consistent field regardless of
            outcome.
        message: Optional human-readable summary of the result.
        data: The actual response payload. Generic so every endpoint can
            declare its own concrete payload type
            (e.g., ``APIResponse[HealthStatus]``).
    """

    success: bool = Field(default=True, description="Always true for successful responses.")
    message: str | None = Field(
        default=None, description="Optional human-readable summary."
    )
    data: DataT | None = Field(default=None, description="Response payload.")


# --------------------------------------------------------------------------
# Router aggregation
# --------------------------------------------------------------------------
# NOTE: `health` is imported here, after `APIResponse` is fully defined
# above, rather than at the top of the module. `app.api.routes.health`
# imports `APIResponse` back from this module, which would otherwise be
# a circular import. Because `APIResponse` is already bound on this
# module by the time Python evaluates the import below, the circular
# reference resolves safely.
from app.api.routes import (
    agents,
    artifacts,
    conversation,
    documents,
    health,
    projects,
    query,
    readiness,
    workflow,
)  # noqa: E402

# All sub-routers are mounted under the versioned API prefix defined once
# in app.core.constants, so a future v2 API is a matter of adding a new
# prefix constant and a parallel router - not touching existing routes.
api_router = APIRouter(prefix=API_V1_PREFIX)

api_router.include_router(health.router)
api_router.include_router(readiness.router)
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(agents.router)
api_router.include_router(query.router)
api_router.include_router(workflow.router)
api_router.include_router(artifacts.router)
api_router.include_router(conversation.router)