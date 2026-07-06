"""Query and retrieval API routes."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.router import APIResponse
from app.application.models import QueryRequest, QueryResponse, QuerySource
from app.dependencies import QueryServiceDependency

router = APIRouter(tags=["Query"])


class QueryAskRequest(BaseModel):
    project_id: str = Field(min_length=1, description="Project identifier to search.")
    question: str = Field(min_length=1, description="Question to answer.")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum context chunks to retrieve.")
    document_type: str | None = Field(default=None, description="Optional document-type filter.")


class QueryMetadataResponse(BaseModel):
    project_id: str = Field(description="Project identifier.")
    source_count: int = Field(description="Number of retrieved sources.")
    model: str | None = Field(default=None, description="LLM model used.")


@router.post(
    "/query",
    response_model=APIResponse[QueryResponse],
    summary="Ask a question",
)
async def ask_question(
    request: QueryAskRequest,
    query_service: QueryServiceDependency,
) -> APIResponse[QueryResponse]:
    try:
        response = query_service.answer_question(
            project_id=request.project_id,
            question=request.question,
            top_k=request.top_k,
            document_type=request.document_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return APIResponse[QueryResponse](message="Question answered.", data=response)


@router.get(
    "/projects/{project_id}/query/sources",
    response_model=APIResponse[list[QuerySource]],
    summary="Return retrieved sources",
)
async def get_retrieved_sources(project_id: str) -> APIResponse[list[QuerySource]]:
    return APIResponse[list[QuerySource]](message="Retrieved sources.", data=[])


@router.get(
    "/projects/{project_id}/query/metadata",
    response_model=APIResponse[QueryMetadataResponse],
    summary="Return metadata",
)
async def get_query_metadata(project_id: str) -> APIResponse[QueryMetadataResponse]:
    return APIResponse[QueryMetadataResponse](
        message="Query metadata retrieved.",
        data=QueryMetadataResponse(project_id=project_id, source_count=0, model=None),
    )
