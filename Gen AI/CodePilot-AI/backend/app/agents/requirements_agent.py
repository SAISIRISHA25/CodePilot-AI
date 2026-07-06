"""
Requirements Agent.

Responsible for analyzing project source documents (business
requirement documents, functional requirement specifications) and
extracting structured, unambiguous software requirements.
"""

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentValidationError
from app.agents.models import AgentInput, AgentMetadata, AgentType
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage
from app.llm.prompt_builder import PromptBuilder

_ROLE_DESCRIPTION = "a senior requirements analyst with deep experience in enterprise SDLC"

_TASK_INSTRUCTIONS = (
    "Analyze the provided project context and extract clear, unambiguous software "
    "requirements. Separate your output into two labeled sections: "
    "'Functional Requirements' and 'Non-Functional Requirements'. For each "
    "requirement, use a numbered list. Explicitly flag any ambiguities, "
    "contradictions, or gaps you find in the source material under a third "
    "section labeled 'Open Questions'."
)


class RequirementsAgent(BaseAgent):
    """Extracts and structures software requirements from project documents."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize the Requirements Agent.

        Args:
            llm_service: The LLM service used to generate this agent's
                output.
        """
        super().__init__(
            llm_service=llm_service,
            metadata=AgentMetadata(
                agent_type=AgentType.REQUIREMENTS,
                agent_name="Requirements Agent",
                description=(
                    "Extracts and structures functional and non-functional "
                    "requirements from uploaded project documents."
                ),
            ),
        )

    def _validate_input(self, agent_input: AgentInput) -> None:
        """Validate that grounding document context was supplied.

        This agent cannot meaningfully extract requirements without
        source material to analyze, so grounding context is mandatory.

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
                "RequirementsAgent requires non-empty document_context to analyze."
            )

    def _build_prompt(self, agent_input: AgentInput) -> list[ChatMessage]:
        """Build the requirements-extraction prompt for this execution.

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