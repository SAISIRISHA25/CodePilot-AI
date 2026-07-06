"""
Documentation Agent.

Responsible for producing clear, professional technical documentation
grounded in the requirements, architecture, and/or code supplied as
context.
"""

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentValidationError
from app.agents.models import AgentInput, AgentMetadata, AgentType
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage
from app.llm.prompt_builder import PromptBuilder

_ROLE_DESCRIPTION = "a senior technical writer specializing in software documentation"

_TASK_INSTRUCTIONS = (
    "Produce clear, professional technical documentation based on the "
    "requirements, architecture, and/or code described in the provided "
    "context. Use appropriate Markdown structure (headings, bullet lists, "
    "code blocks where relevant). Write for an audience of engineers "
    "unfamiliar with this specific project. Do not describe functionality "
    "that is not supported by the provided context."
)


class DocumentationAgent(BaseAgent):
    """Produces technical documentation grounded in project context."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize the Documentation Agent.

        Args:
            llm_service: The LLM service used to generate this agent's
                output.
        """
        super().__init__(
            llm_service=llm_service,
            metadata=AgentMetadata(
                agent_type=AgentType.DOCUMENTATION,
                agent_name="Documentation Agent",
                description=(
                    "Produces clear technical documentation grounded in "
                    "requirements, architecture, and code."
                ),
            ),
        )

    def _validate_input(self, agent_input: AgentInput) -> None:
        """Validate that grounding document context was supplied.

        Documentation written without source material to document would
        be fabricated, so grounding context is mandatory.

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
                "DocumentationAgent requires non-empty document_context to document."
            )

    def _build_prompt(self, agent_input: AgentInput) -> list[ChatMessage]:
        """Build the documentation-generation prompt for this execution.

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