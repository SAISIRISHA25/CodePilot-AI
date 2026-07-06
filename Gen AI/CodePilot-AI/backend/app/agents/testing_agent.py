"""
Testing Agent.

Responsible for designing test plans and test cases - unit,
integration, and edge cases - grounded in the requirements and/or code
supplied as context.
"""

from app.agents.base_agent import BaseAgent
from app.agents.exceptions import AgentValidationError
from app.agents.models import AgentInput, AgentMetadata, AgentType
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage
from app.llm.prompt_builder import PromptBuilder

_ROLE_DESCRIPTION = "a senior QA engineer specializing in comprehensive test design"

_TASK_INSTRUCTIONS = (
    "Design a thorough test plan for the requirements and/or code described "
    "in the provided context. Structure your response with labeled sections: "
    "'Unit Test Cases', 'Integration Test Cases', and 'Edge Cases & Negative "
    "Scenarios'. For each test case, state the scenario, the expected "
    "outcome, and why it matters. Do not assume behavior that is not "
    "supported by the provided context."
)


class TestingAgent(BaseAgent):
    """Designs test plans and test cases grounded in requirements/code context."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize the Testing Agent.

        Args:
            llm_service: The LLM service used to generate this agent's
                output.
        """
        super().__init__(
            llm_service=llm_service,
            metadata=AgentMetadata(
                agent_type=AgentType.TESTING,
                agent_name="Testing Agent",
                description=(
                    "Designs unit, integration, and edge-case test plans "
                    "grounded in requirements and/or code."
                ),
            ),
        )

    def _validate_input(self, agent_input: AgentInput) -> None:
        """Validate that grounding document context was supplied.

        Test cases designed without requirements or code to test against
        would be speculative, so grounding context is mandatory.

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
                "TestingAgent requires non-empty document_context to design tests against."
            )

    def _build_prompt(self, agent_input: AgentInput) -> list[ChatMessage]:
        """Build the test-design prompt for this execution.

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