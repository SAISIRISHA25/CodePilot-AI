"""
Health and version endpoints.

These endpoints are the minimum viable observability surface for any
enterprise API: a liveness/health check for load balancers and
orchestrators (e.g., Docker healthchecks, future Kubernetes probes), and
a version endpoint for verifying exactly which build is deployed.

No business logic lives here - this module only reports on the
application's own status and metadata.
"""

import os
from datetime import UTC, datetime
from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.router import APIResponse
from app.core.version import get_version_info
from app.dependencies import SettingsDependency

router = APIRouter(tags=["Health"])


class HealthStatus(BaseModel):
    """Payload describing the current health of the application.

    Attributes:
        status: A short status string. ``"ok"`` indicates the API
            process is up and able to serve requests. Future modules
            may extend this to report on downstream dependency health
            (e.g., ChromaDB, SQLite connectivity) without changing this
            endpoint's contract - only this model's fields would grow.
        environment: The current deployment environment, useful for
            quickly confirming which environment a health check hit.
        timestamp: UTC timestamp of when the health check was evaluated.
    """

    status: str = Field(description="Overall health status, e.g. 'ok'.")
    environment: str = Field(description="Current deployment environment.")
    timestamp: datetime = Field(description="UTC timestamp of this health check.")


class VersionInfo(BaseModel):
    """Payload describing the running application's version metadata.

    Attributes:
        version: Semantic version of the backend.
        build_stage: Human-readable build stage label.
        application_name: The configured application name.
    """

    version: str = Field(description="Semantic version of the backend.")
    build_stage: str = Field(description="Current build stage label.")
    application_name: str = Field(description="Configured application name.")


@router.get(
    "/health",
    response_model=APIResponse[HealthStatus],
    summary="Liveness/health check",
)
async def health_check(settings: SettingsDependency) -> APIResponse[HealthStatus]:
    """Report whether the application process is up and healthy.

    Intended for use by load balancers, container orchestrators, and
    uptime monitors. Deliberately lightweight - it does not (yet) probe
    downstream dependencies such as ChromaDB or SQLite, since those are
    out of scope for this foundation module.

    Args:
        settings: Injected, cached application settings.

    Returns:
        APIResponse[HealthStatus]: A standard success envelope wrapping
        the current health status.
    """
    health_status = HealthStatus(
        status="ok",
        environment=settings.app.environment.value,
        timestamp=datetime.now(UTC),
    )
    return APIResponse[HealthStatus](message="Service is healthy.", data=health_status)


@router.get(
    "/version",
    response_model=APIResponse[VersionInfo],
    summary="Application version metadata",
)
async def version(settings: SettingsDependency) -> APIResponse[VersionInfo]:
    """Report the running application's version metadata.

    Args:
        settings: Injected, cached application settings.

    Returns:
        APIResponse[VersionInfo]: A standard success envelope wrapping
        the current version metadata.
    """
    version_info = get_version_info()
    payload = VersionInfo(
        version=version_info["version"],
        build_stage=version_info["build_stage"],
        application_name=settings.app.name,
    )
    return APIResponse[VersionInfo](message="Version metadata retrieved.", data=payload)


class SystemLogs(BaseModel):
    """Payload containing server log lines."""
    lines: List[str] = Field(description="List of log lines from the system log file.")


@router.get(
    "/system/logs",
    response_model=APIResponse[SystemLogs],
    summary="Retrieve backend system logs",
)
async def get_system_logs(
    limit: int = Query(default=100, ge=1, le=1000, description="Max number of log lines to retrieve")
) -> APIResponse[SystemLogs]:
    """Read the last N lines from the data/codepilot.log log file."""
    log_file = "data/codepilot.log"
    lines = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                lines = [line.strip() for line in all_lines[-limit:]]
        except Exception as exc:
            lines = [f"Error reading log file: {exc}"]
    else:
        lines = ["Log file data/codepilot.log does not exist yet. Perform some actions to write logs."]
        
    return APIResponse[SystemLogs](
        message="System logs retrieved successfully.",
        data=SystemLogs(lines=lines)
    )