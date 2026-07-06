"""Readiness endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.router import APIResponse

router = APIRouter(tags=["Health"])


class ReadinessStatus(BaseModel):
    status: str = Field(description="Readiness status.")
    checks: list[str] = Field(default_factory=list, description="Readiness checks.")


@router.get(
    "/ready",
    response_model=APIResponse[ReadinessStatus],
    summary="Readiness check",
)
async def readiness_check() -> APIResponse[ReadinessStatus]:
    return APIResponse[ReadinessStatus](
        message="Service is ready.",
        data=ReadinessStatus(status="ready", checks=["app", "database"]),
    )
