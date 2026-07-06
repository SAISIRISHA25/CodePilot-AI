from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.api.router import APIResponse
from app.dependencies import ArtifactRepositoryDependency

router = APIRouter(tags=["Artifacts"])


class ArtifactItem(BaseModel):
    id: str = Field(description="Artifact identifier.")
    name: str = Field(description="Artifact name.")
    content_type: str | None = Field(default=None, description="Artifact content type.")


@router.get(
    "/artifacts",
    response_model=APIResponse[list[ArtifactItem]],
    summary="List generated artifacts",
)
async def list_artifacts(
    artifact_repository: ArtifactRepositoryDependency,
    project_id: str | None = None,
) -> APIResponse[list[ArtifactItem]]:
    records = artifact_repository.list_artifacts(project_id=project_id)
    data = [
        ArtifactItem(
            id=str(r["id"]),
            name=str(r["name"]),
            content_type=r.get("content_type"),
        )
        for r in records
    ]
    return APIResponse[list[ArtifactItem]](message="Artifacts retrieved.", data=data)


@router.get(
    "/artifacts/{artifact_id}",
    summary="Download artifact",
)
async def download_artifact(
    artifact_id: str,
    artifact_repository: ArtifactRepositoryDependency,
) -> Response:
    record = artifact_repository.get_artifact(artifact_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    media_type = str(record.get("content_type") or "text/plain")
    return Response(content=str(record["content"]), media_type=media_type)


@router.delete(
    "/artifacts/{artifact_id}",
    response_model=APIResponse[dict[str, bool]],
    summary="Delete artifact",
)
async def delete_artifact(
    artifact_id: str,
    artifact_repository: ArtifactRepositoryDependency,
) -> APIResponse[dict[str, bool]]:
    deleted = artifact_repository.delete_artifact(artifact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return APIResponse[dict[str, bool]](message="Artifact deleted.", data={"deleted": deleted})
