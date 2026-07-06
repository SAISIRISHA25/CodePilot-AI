"""
Agents package for CodePilot AI.

Provides the seven SDLC agents, each a thin, focused subclass of
``BaseAgent`` implementing exactly one responsibility:

    RequirementsAgent    - extracts structured requirements from
                            project documents.
    ArchitectureAgent    - proposes software architecture.
    PlanningAgent        - breaks work into a sequenced implementation
                            plan.
    CodingAgent          - generates source code artifacts.
    TestingAgent         - designs test plans and test cases.
    DocumentationAgent   - produces technical documentation.
    ReviewAgent          - critically reviews generated artifacts.

Every agent receives an ``LLMService`` through constructor injection and
communicates exclusively through the typed models in ``models.py``
(``AgentInput`` in, ``AgentExecutionResult`` out). This package contains
no LangGraph orchestration, no FastAPI routes, and no persistence code -
composing these agents into a multi-step workflow is the responsibility
of a future orchestration module.

Typical usage (illustrative only - not implemented in this package):

    llm_service = LLMService()
    agent = RequirementsAgent(llm_service=llm_service)
    result = agent.execute(
        AgentInput(
            task_description="Extract requirements related to authentication.",
            context=AgentContext(project_id="proj-123", document_context=doc_text),
        )
    )
"""

from app.agents.architecture_agent import ArchitectureAgent
from app.agents.base_agent import BaseAgent
from app.agents.coding_agent import CodingAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.exceptions import (
    AgentError,
    AgentExecutionError,
    AgentValidationError,
    UnsupportedAgentError,
)
from app.agents.models import (
    AgentContext,
    AgentExecutionResult,
    AgentInput,
    AgentMetadata,
    AgentOutput,
    AgentType,
)
from app.agents.planning_agent import PlanningAgent
from app.agents.requirements_agent import RequirementsAgent
from app.agents.review_agent import ReviewAgent
from app.agents.testing_agent import TestingAgent

__all__ = [
    # Base
    "BaseAgent",
    # Concrete agents
    "RequirementsAgent",
    "ArchitectureAgent",
    "PlanningAgent",
    "CodingAgent",
    "TestingAgent",
    "DocumentationAgent",
    "ReviewAgent",
    # Models
    "AgentType",
    "AgentMetadata",
    "AgentContext",
    "AgentInput",
    "AgentOutput",
    "AgentExecutionResult",
    # Exceptions
    "AgentError",
    "AgentValidationError",
    "AgentExecutionError",
    "UnsupportedAgentError",
]