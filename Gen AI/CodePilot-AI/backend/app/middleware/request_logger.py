"""
Request correlation ID and structured request logging middleware.

Every enterprise API needs a way to trace a single request across logs,
error reports, and (later) LangSmith traces. This middleware assigns a
unique correlation ID to every inbound request, exposes it on
``request.state.request_id``, echoes it back as a response header, and
emits a structured log line for both the start and completion of the
request (including latency and status code).

Design decision:
    Implemented as Starlette's ``BaseHTTPMiddleware`` rather than a raw
    ASGI middleware for readability and because request/response body
    access is not required here - only metadata (method, path, status,
    timing). This keeps the middleware simple and easy to reason about,
    which matters for a capstone timeline.
"""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Module-level logger, namespaced so log output can be filtered/routed
# independently of other application loggers (e.g., agent execution logs).
logger = logging.getLogger("codepilot.request")

# Header name used to propagate the correlation ID to clients and, in a
# distributed deployment, to downstream services.
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns a correlation ID to each request and logs its lifecycle.

    Attaches ``request.state.request_id`` for downstream use (route
    handlers, exception handlers) and logs a single structured entry per
    request containing method, path, status code, and duration in
    milliseconds.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process an incoming request, injecting a correlation ID.

        Args:
            request: The incoming HTTP request.
            call_next: The next handler in the middleware chain.

        Returns:
            Response: The outgoing HTTP response, with the correlation
            ID attached as a response header.
        """
        # Prefer a client-supplied request ID if present (useful when
        # this API sits behind a gateway that already generates one),
        # otherwise mint a new UUID4.
        incoming_request_id = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming_request_id or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        logger.info(
            "request.started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            # Log the failure with timing before re-raising so the
            # global exception handlers (exceptions/handlers.py) can
            # still produce the client-facing error response. This
            # middleware's job is observability, not error translation.
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "request.failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id

        logger.info(
            "request.completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return response