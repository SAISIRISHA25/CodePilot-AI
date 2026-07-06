"""
Coding Agent.

Responsible for generating source code artifacts (as text content)
grounded in the architecture, plan, and requirements supplied as
context. This agent produces code as generated text output only - it
never executes, persists, or writes code to disk. That is intentionally
out of scope for this package.
"""

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentValidationError
from app.agents.models import AgentInput, AgentMetadata, AgentType
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage
from app.llm.prompt_builder import PromptBuilder

_ROLE_DESCRIPTION = "a senior software developer who writes clean, production-ready code"

_TASK_INSTRUCTIONS = (
    "Generate source code that implements the requirements, architecture, "
    "and/or plan described in the provided context. Follow Clean Architecture "
    "and SOLID principles. Include clear docstrings and comments explaining "
    "non-obvious decisions. Present the code in fenced code blocks with the "
    "correct language identifier. Do not fabricate requirements that are not "
    "present in the provided context, and do not claim to have executed or "
    "tested the code - you are generating source text only."
)


class CodingAgent(BaseAgent):
    """Generates source code artifacts grounded in architecture/plan context."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize the Coding Agent.

        Args:
            llm_service: The LLM service used to generate this agent's
                output.
        """
        super().__init__(
            llm_service=llm_service,
            metadata=AgentMetadata(
                agent_type=AgentType.CODING,
                agent_name="Coding Agent",
                description=(
                    "Generates source code artifacts grounded in "
                    "requirements, architecture, and implementation plans."
                ),
            ),
        )

    def _validate_input(self, agent_input: AgentInput) -> None:
        """Validate that grounding document context was supplied.

        Code generated with no architecture or requirements to ground it
        in is unreliable by construction, so grounding context is
        mandatory.

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
                "CodingAgent requires non-empty document_context to ground code generation."
            )

    def _build_prompt(self, agent_input: AgentInput) -> list[ChatMessage]:
        """Build the code-generation prompt for this execution.

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