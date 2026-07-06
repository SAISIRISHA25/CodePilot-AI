"""Typed request and response models used by the application services."""

from pydantic import BaseModel, Field

from app.agents.models import AgentType
from app.llm.models import TokenUsage


class AgentRequest(BaseModel):
    """Request model for routing a single agent execution."""

    agent_type: AgentType = Field(description="The agent to execute.")
    task_description: str = Field(description="The task to pass to the agent.")
    project_id: str = Field(description="The owning project identifier.")
    document_context: str | None = Field(
        default=None, description="Optional grounding context for the agent."
    )
    additional_context: dict[str, str] | None = Field(
        default=None, description="Optional additional context values."
    )
    model_override: str | None = Field(default=None, description="Optional model override.")
    temperature_override: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Optional temperature override."
    )


class AgentResponse(BaseModel):
    """Response payload returned after a single agent dispatch."""

    agent_type: AgentType = Field(description="The agent that executed.")
    agent_name: str = Field(description="Human-friendly agent name.")
    content: str = Field(description="Text content returned by the agent.")
    token_usage: TokenUsage | None = Field(
        default=None, description="Token usage information if available."
    )
    execution_time_ms: float | None = Field(
        default=None, description="Execution duration in milliseconds."
    )


class IngestionResult(BaseModel):
    """Summary of a completed document ingestion pipeline run."""

    project_id: str = Field(description="Owning project identifier.")
    filename: str = Field(description="Name of the ingested file.")
    document_type: str = Field(description="Type of the ingested document.")
    source_document_id: str = Field(description="Identifier for the source document.")
    total_chunks: int = Field(ge=0, description="Number of chunks stored.")
    chunk_ids: list[str] = Field(default_factory=list, description="Stored chunk IDs.")
    embedding_model: str | None = Field(default=None, description="Embedding model used.")
    ingested_at: str | None = Field(default=None, description="Ingestion timestamp.")


class QueryRequest(BaseModel):
    """Request model for question answering over project data."""

    project_id: str = Field(description="The project to search.")
    question: str = Field(description="The natural-language question to answer.")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum context chunks to retrieve.")
    document_type: str | None = Field(default=None, description="Optional document-type filter.")


class QuerySource(BaseModel):
    """A single cited source returned with a generated answer."""

    filename: str = Field(description="Source document filename.")
    chunk_index: int = Field(ge=0, description="Chunk index within the source document.")
    relevance_score: float = Field(description="Retrieval relevance score.")


class QueryResponse(BaseModel):
    """Response model for a grounded question-answering interaction."""

    question: str = Field(description="The original question.")
    answer: str = Field(description="The generated answer.")
    sources: list[QuerySource] = Field(default_factory=list, description="Cited sources.")
    token_usage: TokenUsage | None = Field(default=None, description="Token usage information.")
    model: str | None = Field(default=None, description="Model used to answer the question.")
