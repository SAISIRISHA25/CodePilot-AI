"""
Review Agent.

Responsible for critically reviewing generated artifacts (code,
architecture proposals, documentation) against best practices, Clean
Architecture, and SOLID principles, grounded in the artifact and any
supporting context supplied.
"""

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentValidationError
from app.agents.models import AgentInput, AgentMetadata, AgentType
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage
from app.llm.prompt_builder import PromptBuilder

_ROLE_DESCRIPTION = "a senior code reviewer with a strong focus on Clean Architecture and SOLID"

_TASK_INSTRUCTIONS = (
    "Critically review the artifact described in the provided context (code, "
    "architecture proposal, or documentation). Structure your response with "
    "labeled sections: 'Strengths', 'Issues Found' (each issue labeled with a "
    "severity of Critical, Major, or Minor), and 'Recommended Changes'. "
    "Evaluate adherence to Clean Architecture, SOLID principles, and general "
    "software engineering best practices. Base your review strictly on the "
    "provided context - do not invent issues unrelated to what was supplied."
)


class ReviewAgent(BaseAgent):
    """Critically reviews generated artifacts against engineering best practices."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize the Review Agent.

        Args:
            llm_service: The LLM service used to generate this agent's
                output.
        """
        super().__init__(
            llm_service=llm_service,
            metadata=AgentMetadata(
                agent_type=AgentType.REVIEW,
                agent_name="Review Agent",
                description=(
                    "Critically reviews generated artifacts for quality, "
                    "best practices, and architectural soundness."
                ),
            ),
        )

    def _validate_input(self, agent_input: AgentInput) -> None:
        """Validate that grounding document context was supplied.

        A review with nothing to review would be fabricated, so
        grounding context is mandatory.

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
                "ReviewAgent requires non-empty document_context containing the artifact to review."
            )

    def _build_prompt(self, agent_input: AgentInput) -> list[ChatMessage]:
        """Build the review prompt for this execution.

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