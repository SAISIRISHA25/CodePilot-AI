"""
Application-wide constants and enumerations.

This module centralizes fixed values used across CodePilot AI so that
"magic strings" (agent names, environment labels, default sizes, API
prefixes) are defined exactly once. Any layer that needs one of these
values imports it from here rather than re-declaring it locally.

Design decision:
    Constants are grouped as Enums where the value represents a closed,
    finite set (e.g., Environment, AgentName). Plain module-level
    constants are used for scalar defaults (e.g., chunk sizes, API
    prefixes) that are not part of a finite categorical set.

    This module MUST remain framework-agnostic (no LangChain, LangGraph,
    or FastAPI imports) so that domain and application layers can safely
    depend on it without violating Clean Architecture boundaries.
"""

from enum import Enum


class Environment(str, Enum):
    """Deployment environment identifiers.

    Inherits from ``str`` so values serialize cleanly in logs, API
    responses, and Pydantic models without extra conversion.
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class AgentName(str, Enum):
    """Canonical names for every AI agent in the SDLC pipeline.

    These values are used as identifiers in audit logs, LangSmith trace
    metadata, and LangGraph node names, ensuring a single consistent
    label is used everywhere an agent is referenced.
    """

    REQUIREMENT_ANALYST = "requirement_analyst"
    SOLUTION_ARCHITECT = "solution_architect"
    DEVELOPER = "developer"
    CODE_REVIEWER = "code_reviewer"
    QA_ENGINEER = "qa_engineer"
    DOCUMENTATION_WRITER = "documentation_writer"
    DEVOPS_ADVISOR = "devops_advisor"


class DocumentType(str, Enum):
    """Supported categories of uploaded project documents.

    Used to drive document-type-aware ingestion behavior (e.g.,
    chunking strategy, retrieval metadata filters) in later modules.
    """

    BUSINESS_REQUIREMENT_DOCUMENT = "business_requirement_document"
    FUNCTIONAL_REQUIREMENT_SPECIFICATION = "functional_requirement_specification"
    ARCHITECTURE_DOCUMENT = "architecture_document"
    API_SPECIFICATION = "api_specification"
    CODING_STANDARDS = "coding_standards"


class PipelineRunStatus(str, Enum):
    """Lifecycle states of a LangGraph pipeline execution.

    Consumed by audit logging and API responses to represent the
    current status of a project's agent pipeline run.
    """

    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


# --------------------------------------------------------------------------
# API constants
# --------------------------------------------------------------------------
# Centralizing the versioned prefix here means the interface layer never
# hardcodes "/api/v1" inline, so a future v2 rollout touches one constant.
API_V1_PREFIX: str = "/api/v1"

# --------------------------------------------------------------------------
# RAG / ingestion defaults
# --------------------------------------------------------------------------
# These are sensible starting defaults for capstone scope. They are
# intentionally defined as constants (not settings) because they are
# implementation defaults, not deployment-environment configuration.
DEFAULT_CHUNK_SIZE: int = 1000
DEFAULT_CHUNK_OVERLAP: int = 200

# --------------------------------------------------------------------------
# Agent execution defaults
# --------------------------------------------------------------------------
# Bounded retry count for LangGraph validation-gate retry edges, preventing
# infinite loops when an agent repeatedly produces schema-invalid output.
DEFAULT_AGENT_MAX_RETRIES: int = 2

# Default LLM sampling temperature for deterministic-leaning agent output.
# Low temperature favors consistency, which matters for structured,
# schema-validated agent responses.
DEFAULT_LLM_TEMPERATURE: float = 0.2

# --------------------------------------------------------------------------
# Schema versioning
# --------------------------------------------------------------------------
# Every agent's Pydantic output schema is tagged with this version string
# in audit logs, allowing future schema evolution to remain traceable.
CURRENT_SCHEMA_VERSION: str = "1.0.0"