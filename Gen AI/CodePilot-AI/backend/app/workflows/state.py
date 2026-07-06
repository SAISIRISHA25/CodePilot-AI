"""
Workflow state schema.

``GraphState`` is the single Pydantic model threaded through every node
of every LangGraph workflow in this package. It is the ONLY thing nodes
exchange - no node ever calls another node's collaborators directly,
and no data crosses a node boundary except through this model.

Design decision:
    ``GraphState`` and every nested value object (``UploadedDocument``,
    ``RetrievedContextItem``, ``WorkflowHistoryEntry``) are declared
    ``frozen=True``. Nodes never mutate state in place (``state.x = y``
    would raise ``ValidationError`` on a frozen model); instead, every
    node builds and returns a new state via
    ``state.model_copy(update={...})`` or an equivalent partial-update
    dict, appending to lists/dicts functionally
    (``state.errors + [new_error]``) rather than mutating them. This
    makes every state transition an explicit, traceable value rather
    than an in-place side effect - important for a workflow package
    whose entire job is coordinating state transitions correctly.
"""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.agents.models import AgentType
from app.core.constants import DocumentType


class WorkflowPhase(str, Enum):
    """The discrete phases a workflow can be in.

    Inherits from ``str`` so values serialize cleanly in logs and in
    any future persisted execution history.
    """

    PENDING = "pending"
    INGESTION = "ingestion"
    RETRIEVAL = "retrieval"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    SAVE_OUTPUT = "save_output"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadedDocument(BaseModel):
    """A single document made available to the workflow for ingestion.

    Attributes:
        file_path: Filesystem path to the document.
        filename: Original filename of the document.
        document_type: Category of the document.
    """

    model_config = ConfigDict(frozen=True)

    file_path: str = Field(description="Filesystem path to the document.")
    filename: str = Field(description="Original filename of the document.")
    document_type: DocumentType = Field(description="Category of the document.")


class RetrievedContextItem(BaseModel):
    """A single retrieved chunk carried in workflow state.

    Mirrors the relevant fields of ``app.rag.models.RetrievalResult``
    without depending on that exact model, keeping this state schema
    self-contained and stable even if the RAG package's internal
    result shape evolves.

    Attributes:
        content: The retrieved chunk's text content.
        filename: The source document's filename.
        chunk_index: The chunk's position within its source document.
        relevance_score: Distance-based relevance score.
    """

    model_config = ConfigDict(frozen=True)

    content: str = Field(description="Retrieved chunk text content.")
    filename: str = Field(description="Filename of the source document.")
    chunk_index: int = Field(ge=0, description="Chunk position within its source document.")
    relevance_score: float = Field(description="Distance-based relevance score.")


class WorkflowHistoryEntry(BaseModel):
    """A single entry in the workflow's conversation/execution history.

    Attributes:
        phase: The workflow phase active when this entry was recorded.
        agent_type: The agent involved, if this entry corresponds to an
            agent execution.
        summary: A short, human-readable summary of what happened.
        occurred_at: UTC timestamp of when this entry was recorded.
    """

    model_config = ConfigDict(frozen=True)

    phase: WorkflowPhase = Field(description="Workflow phase active at this entry.")
    agent_type: AgentType | None = Field(
        default=None, description="Agent involved, if applicable."
    )
    summary: str = Field(min_length=1, description="Short summary of what happened.")
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="UTC timestamp of this entry."
    )


class GraphState(BaseModel):
    """The complete, immutable state threaded through a LangGraph workflow.

    Attributes:
        project_id: The project this workflow execution belongs to.
        user_prompt: The original user-supplied prompt/task that started
            this workflow.
        uploaded_documents: Documents available for ingestion.
        retrieved_context: Chunks retrieved so far, used to ground
            subsequent agent nodes.
        current_phase: The workflow's current phase.
        generated_outputs: Accumulated output content, keyed by phase or
            agent name (e.g., ``{"requirements": "...", "architecture": "..."}``).
        conversation_history: Ordered log of what has happened so far in
            this execution.
        selected_agent: The agent type currently selected for dispatch,
            if any.
        errors: Accumulated error messages from any failed step.
        metadata: Free-form supplementary key-value state.
    """

    model_config = ConfigDict(frozen=True)

    project_id: str = Field(min_length=1, description="Owning project identifier.")
    user_prompt: str = Field(default="", description="Original user-supplied prompt/task.")
    uploaded_documents: list[UploadedDocument] = Field(
        default_factory=list, description="Documents available for ingestion."
    )
    retrieved_context: list[RetrievedContextItem] = Field(
        default_factory=list, description="Chunks retrieved so far."
    )
    current_phase: WorkflowPhase = Field(
        default=WorkflowPhase.PENDING, description="Current workflow phase."
    )
    generated_outputs: dict[str, str] = Field(
        default_factory=dict, description="Accumulated output content, keyed by phase/agent."
    )
    conversation_history: list[WorkflowHistoryEntry] = Field(
        default_factory=list, description="Ordered log of workflow execution events."
    )
    selected_agent: AgentType | None = Field(
        default=None, description="Agent type currently selected for dispatch."
    )
    errors: list[str] = Field(default_factory=list, description="Accumulated error messages.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Free-form supplementary key-value state."
    )