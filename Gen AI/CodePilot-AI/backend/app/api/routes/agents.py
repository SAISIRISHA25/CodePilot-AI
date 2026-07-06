"""Agent execution and discovery API routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.agents.models import AgentType
from app.api.router import APIResponse
from app.application.models import AgentRequest, AgentResponse
from app.dependencies import AgentRouterDependency, ArtifactRepositoryDependency, get_retriever
from app.rag.retriever import RetrieverService
from app.rag.models import RetrievalQuery

router = APIRouter(tags=["Agents"])


class AgentExecutionRequest(BaseModel):
    agent_type: AgentType = Field(description="The agent to execute.")
    task_description: str = Field(min_length=1, description="The task to pass to the agent.")
    project_id: str = Field(min_length=1, description="The owning project identifier.")
    document_context: str | None = Field(default=None, description="Optional grounding context.")
    additional_context: dict[str, str] | None = Field(default=None, description="Optional context values.")


class AgentListItem(BaseModel):
    agent_type: AgentType = Field(description="Agent type.")
    name: str = Field(description="Human-readable agent name.")


@router.post(
    "/agents/execute",
    response_model=APIResponse[AgentResponse],
    summary="Execute a specific agent",
)
async def execute_agent(
    request: AgentExecutionRequest,
    agent_router: AgentRouterDependency,
    artifact_repository: ArtifactRepositoryDependency,
    retriever_service: RetrieverService = Depends(get_retriever),
) -> APIResponse[AgentResponse]:
    # Auto-retrieve grounding context from ChromaDB if generic/empty
    doc_context = request.document_context
    if not doc_context or doc_context == "Functional Specifications":
        try:
            retrieval_query = RetrievalQuery(
                project_id=request.project_id,
                query_text=request.task_description,
                top_k=5,
            )
            chunks = retriever_service.retrieve(retrieval_query)
            if chunks:
                doc_context = "\n\n".join(c.content for c in chunks)
        except Exception:
            pass

    try:
        response = agent_router.dispatch(
            AgentRequest(
                agent_type=request.agent_type,
                task_description=request.task_description,
                project_id=request.project_id,
                document_context=doc_context,
                additional_context=request.additional_context,
            )
        )
        # Create and persist artifact
        artifact_repository.create_artifact(
            project_id=request.project_id,
            name=request.agent_type.value,
            content=response.content,
            content_type="text/markdown",
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return APIResponse[AgentResponse](message="Agent executed and artifact saved.", data=response)


@router.get(
    "/agents",
    response_model=APIResponse[list[AgentListItem]],
    summary="List available agents",
)
async def list_agents() -> APIResponse[list[AgentListItem]]:
    items = [
        AgentListItem(agent_type=AgentType.REQUIREMENTS, name="Requirements Agent"),
        AgentListItem(agent_type=AgentType.ARCHITECTURE, name="Architecture Agent"),
        AgentListItem(agent_type=AgentType.PLANNING, name="Planning Agent"),
        AgentListItem(agent_type=AgentType.CODING, name="Coding Agent"),
        AgentListItem(agent_type=AgentType.TESTING, name="Testing Agent"),
        AgentListItem(agent_type=AgentType.DOCUMENTATION, name="Documentation Agent"),
        AgentListItem(agent_type=AgentType.REVIEW, name="Review Agent"),
    ]
    return APIResponse[list[AgentListItem]](message="Agents retrieved.", data=items)
