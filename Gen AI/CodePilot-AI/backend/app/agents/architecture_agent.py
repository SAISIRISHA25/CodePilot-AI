"""
Architecture Agent.

Responsible for proposing a software architecture - components,
patterns, and technology choices - grounded in requirements and any
existing architecture documentation supplied as context.
"""

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentValidationError
from app.agents.models import AgentInput, AgentMetadata, AgentType
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage
from app.llm.prompt_builder import PromptBuilder

_ROLE_DESCRIPTION = "a senior solution architect specializing in Clean Architecture and SOLID design"

_TASK_INSTRUCTIONS = (
    "Propose a software architecture that satisfies the requirements and "
    "constraints described in the provided context. Structure your response "
    "with labeled sections: 'Proposed Components', 'Architectural Pattern & "
    "Rationale', 'Key Design Decisions', and 'Risks & Trade-offs'. Explicitly "
    "justify how your proposal supports Clean Architecture and SOLID "
    "principles. Do not invent requirements that are not present in the "
    "provided context."
)


class ArchitectureAgent(BaseAgent):
    """Proposes software architecture grounded in requirements context."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize the Architecture Agent.

        Args:
            llm_service: The LLM service used to generate this agent's
                output.
        """
        super().__init__(
            llm_service=llm_service,
            metadata=AgentMetadata(
                agent_type=AgentType.ARCHITECTURE,
                agent_name="Architecture Agent",
                description=(
                    "Proposes software architecture, components, and design "
                    "patterns grounded in project requirements."
                ),
            ),
        )

    def _validate_input(self, agent_input: AgentInput) -> None:
        """Validate that grounding document context was supplied.

        This agent must not propose architecture in a vacuum - it needs
        requirements or existing architecture material to ground its
        proposal in.

        Args:
            agent_input: The input to validate.

        Raises:
            AgentValidationError: If ``document_context`` is missing or
                blank.
        """
        super()._validate_input(agent_input)
        if (
            not agent_input.context.document_context
            or not agent_input.context.document_context.strip()
        ):
            raise AgentValidationError(
                "ArchitectureAgent requires non-empty document_context to ground its proposal."
            )

    def _build_prompt(self, agent_input: AgentInput) -> list[ChatMessage]:
        """Build the architecture-proposal prompt for this execution.

        Args:
            agent_input: The structured input for this execution.

        Returns:
            list[ChatMessage]: The conversation to send to the LLM.
        """
        return PromptBuilder.build_document_grounded_prompt(
            task_instructions=_TASK_INSTRUCTIONS,
            document_context=agent_input.context.document_context or "",
            user_request=agent_input.task_description,
            system_role_description=_ROLE_DESCRIPTION,
        )