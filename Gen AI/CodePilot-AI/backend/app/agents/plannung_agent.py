"""
Planning Agent.

Responsible for breaking down requirements and architecture into a
sequenced, actionable implementation plan - without writing any code
itself. That responsibility belongs to ``CodingAgent``.
"""

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentValidationError
from app.agents.models import AgentInput, AgentMetadata, AgentType
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage
from app.llm.prompt_builder import PromptBuilder

_ROLE_DESCRIPTION = "a senior technical project planner experienced in agile SDLC delivery"

_TASK_INSTRUCTIONS = (
    "Break the provided requirements and/or architecture into a sequenced, "
    "actionable implementation plan. Structure your response with labeled "
    "sections: 'Work Breakdown' (a numbered list of discrete implementation "
    "tasks), 'Suggested Sequencing & Dependencies', and 'Notable Risks to "
    "Delivery'. Do not write any source code - this plan describes what work "
    "needs to happen, not how to implement it line by line."
)


class PlanningAgent(BaseAgent):
    """Produces a sequenced implementation plan from requirements/architecture."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize the Planning Agent.

        Args:
            llm_service: The LLM service used to generate this agent's
                output.
        """
        super().__init__(
            llm_service=llm_service,
            metadata=AgentMetadata(
                agent_type=AgentType.PLANNING,
                agent_name="Planning Agent",
                description=(
                    "Breaks down requirements and architecture into a "
                    "sequenced, actionable implementation plan."
                ),
            ),
        )

    def _validate_input(self, agent_input: AgentInput) -> None:
        """Validate that grounding document context was supplied.

        A plan without requirements or architecture to plan against is
        meaningless, so grounding context is mandatory.

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
                "PlanningAgent requires non-empty document_context to plan against."
            )

    def _build_prompt(self, agent_input: AgentInput) -> list[ChatMessage]:
        """Build the implementation-planning prompt for this execution.

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