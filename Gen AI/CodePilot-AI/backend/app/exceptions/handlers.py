"""
Global exception handling for the CodePilot AI API.

Centralizes translation of exceptions into consistent, client-facing
JSON error responses. This is the only place in the interface layer
that should ever catch broad exception types - every other module lets
exceptions propagate here.

Design decision:
    A single ``ErrorResponse`` schema is used for every error case
    (validation errors, HTTP exceptions, and unhandled exceptions) so
    API consumers (the React frontend, or any future client) can rely on
    one consistent error shape regardless of failure type. Internal
    exception details are logged in full server-side but never leaked
    to the client in production, preventing accidental information
    disclosure.
"""

import logging
from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("codepilot.errors")


class ErrorDetail(BaseModel):
    """A single structured error detail entry.

    Used primarily to carry field-level validation error information in
    a predictable shape, rather than passing through FastAPI's raw
    validation error structure verbatim.
    """

    field: str | None = Field(
        default=None, description="The field the error relates to, if any."
    )
    message: str = Field(description="Human-readable description of the error.")


class ErrorResponse(BaseModel):
    """Standard error response envelope returned by every failure path.

    Attributes:
        success: Always ``False`` for error responses. Mirrors the
            ``success`` flag on the standard success envelope
            (``app.api.router.APIResponse``) so clients can branch on
            one consistent field.
        error_code: A short, stable, machine-readable error identifier
            (e.g., ``"VALIDATION_ERROR"``, ``"INTERNAL_SERVER_ERROR"``).
        message: A human-readable summary of what went wrong.
        details: Optional list of granular error details (e.g., which
            fields failed validation).
        request_id: The correlation ID for this request, allowing
            support/engineering to locate the corresponding log entries.
        timestamp: UTC timestamp of when the error was generated.
    """

    success: bool = Field(default=False, description="Always false for errors.")
    error_code: str = Field(description="Stable, machine-readable error code.")
    message: str = Field(description="Human-readable error summary.")
    details: list[ErrorDetail] = Field(
        default_factory=list, description="Granular error details, if any."
    )
    request_id: str = Field(description="Correlation ID for this request.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when the error occurred.",
    )


def _get_request_id(request: Request) -> str:
    """Safely extract the correlation ID attached by the logging middleware.

    Args:
        request: The current request.

    Returns:
        str: The request's correlation ID, or ``"unknown"`` if the
        logging middleware did not run (defensive fallback, e.g., in
        isolated unit tests of a handler).
    """
    return getattr(request.state, "request_id", "unknown")


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation failures (invalid query/body/path params).

    Args:
        request: The request that failed validation.
        exc: The validation error raised by FastAPI/Pydantic.

    Returns:
        JSONResponse: A 422 response using the standard error envelope,
        with one ``ErrorDetail`` per invalid field.
    """
    request_id = _get_request_id(request)
    details = [
        ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
        )
        for error in exc.errors()
    ]

    logger.warning(
        "request.validation_error",
        extra={"request_id": request_id, "errors": exc.errors()},
    )

    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="One or more fields failed validation.",
        details=details,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode="json"),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle explicitly raised HTTP exceptions (e.g., 404, 403, 409).

    Args:
        request: The request that triggered the exception.
        exc: The HTTP exception raised by a route handler or dependency.

    Returns:
        JSONResponse: A response with the exception's original status
        code, using the standard error envelope.
    """
    request_id = _get_request_id(request)

    logger.info(
        "request.http_exception",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )

    error_response = ErrorResponse(
        error_code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for any exception not otherwise handled.

    This is the final safety net: it guarantees the API never leaks a
    raw traceback or an unstructured 500 response to a client. Full
    exception details are logged server-side (with stack trace) for
    debugging; the client only receives a generic, non-sensitive message.

    Args:
        request: The request being processed when the exception occurred.
        exc: The unhandled exception.

    Returns:
        JSONResponse: A 500 response using the standard error envelope.
    """
    request_id = _get_request_id(request)

    # Full stack trace goes to the server-side logs only.
    logger.exception(
        "request.unhandled_exception",
        extra={"request_id": request_id},
    )

    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please contact support with the request ID.",
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register every global exception handler on the given FastAPI app.

    Centralizing registration in one function keeps ``main.py``'s
    application factory clean and makes the full set of handled
    exception types discoverable from a single call site.

    Args:
        app: The FastAPI application instance to register handlers on.
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    