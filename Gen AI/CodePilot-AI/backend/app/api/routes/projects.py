"""Project management API routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.api.router import APIResponse
from app.dependencies import ProjectServiceDependency, get_vector_store_gateway
from app.rag.vector_store import VectorStoreService

router = APIRouter(tags=["Projects"])


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, description="Project display name.")
    description: str | None = Field(default=None, description="Project description.")


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, description="Updated project name.")
    description: str | None = Field(default=None, description="Updated project description.")


class ProjectResponse(BaseModel):
    id: str = Field(description="Project identifier.")
    name: str = Field(description="Project display name.")
    description: str | None = Field(default=None, description="Project description.")
    created_at: str = Field(description="Creation timestamp.")
    updated_at: str = Field(description="Last update timestamp.")


@router.post(
    "/projects",
    response_model=APIResponse[ProjectResponse],
    summary="Create a project",
)
async def create_project(
    request: ProjectCreateRequest,
    project_service: ProjectServiceDependency,
) -> APIResponse[ProjectResponse]:
    created = project_service.create_project(name=request.name, description=request.description)
    return APIResponse[ProjectResponse](
        message="Project created.",
        data=ProjectResponse(**created),
    )


@router.get(
    "/projects",
    response_model=APIResponse[list[ProjectResponse]],
    summary="List projects",
)
async def list_projects(
    project_service: ProjectServiceDependency,
) -> APIResponse[list[ProjectResponse]]:
    projects = [ProjectResponse(**item) for item in project_service.list_projects()]
    return APIResponse[list[ProjectResponse]](message="Projects retrieved.", data=projects)


@router.get(
    "/projects/{project_id}",
    response_model=APIResponse[ProjectResponse],
    summary="Get a project",
)
async def get_project(
    project_id: str,
    project_service: ProjectServiceDependency,
) -> APIResponse[ProjectResponse]:
    project = project_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return APIResponse[ProjectResponse](message="Project retrieved.", data=ProjectResponse(**project))


@router.patch(
    "/projects/{project_id}",
    response_model=APIResponse[ProjectResponse],
    summary="Update a project",
)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    project_service: ProjectServiceDependency,
) -> APIResponse[ProjectResponse]:
    updated = project_service.update_project(
        project_id,
        name=request.name,
        description=request.description,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return APIResponse[ProjectResponse](message="Project updated.", data=ProjectResponse(**updated))


@router.delete(
    "/projects/{project_id}",
    response_model=APIResponse[dict[str, bool]],
    summary="Delete a project",
)
async def delete_project(
    project_id: str,
    project_service: ProjectServiceDependency,
    vector_store: VectorStoreService = Depends(get_vector_store_gateway),
) -> APIResponse[dict[str, bool]]:
    # Delete chunks from vector store first
    try:
        vector_store.delete_project_chunks(project_id)
    except Exception as exc:
        pass

    deleted = project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return APIResponse[dict[str, bool]](message="Project deleted.", data={"deleted": True})
