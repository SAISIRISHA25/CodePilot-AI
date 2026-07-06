"""Typed models shared across the agents package and its callers."""

from enum import Enum

from pydantic import BaseModel, Field

from app.llm.models import TokenUsage


class AgentType(str, Enum):
    """Canonical agent identifiers used throughout the workflow stack."""

    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"


class AgentMetadata(BaseModel):
    """Identity data for a single agent instance."""

    agent_type: AgentType = Field(description="The agent's canonical identifier.")
    agent_name: str = Field(description="Display name for this agent.")
    description: str = Field(description="Short summary of the agent's responsibility.")


class AgentContext(BaseModel):
    """Context supplied to an agent execution."""

    project_id: str = Field(description="Project identifier for the execution.")
    document_context: str | None = Field(
        default=None, description="Grounding document text or prior artifact content."
    )
    additional_context: dict[str, str] | None = Field(
        default=None, description="Optional free-form context values.")


class AgentInput(BaseModel):
    """Input payload used to invoke an agent."""

    task_description: str = Field(description="The task the agent should perform.")
    context: AgentContext = Field(description="Context to ground the agent's work.")
    model_override: str | None = Field(default=None, description="Optional model override.")
    temperature_override: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Optional temperature override."
    )


class AgentOutput(BaseModel):
    """Structured output produced by an agent."""

    content: str = Field(description="The generated agent output text.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional output metadata."
    )


class AgentExecutionResult(BaseModel):
    """Full execution record returned by a completed agent run."""

    agent_metadata: AgentMetadata = Field(description="Identity of the agent that ran.")
    agent_input: AgentInput = Field(description="The input that produced this result.")
    output: AgentOutput = Field(description="Structured output emitted by the agent.")
    token_usage: TokenUsage = Field(description="Token accounting for the run.")
    execution_time_ms: float = Field(description="Execution duration in milliseconds.")
