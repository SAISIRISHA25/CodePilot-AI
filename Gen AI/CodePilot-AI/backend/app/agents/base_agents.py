"""
Abstract base class for every SDLC agent.

``BaseAgent`` defines the Template Method every concrete agent follows:
build a prompt, invoke the LLM, parse the result into a typed output.
Concrete agents (``RequirementsAgent``, ``ArchitectureAgent``, etc.)
only need to implement ``_build_prompt`` - the rest of the execution
lifecycle (validation, LLM invocation, error translation, timing,
result assembly) is handled once, here, and inherited by every agent.

Design decision:
    This class receives an ``LLMService`` instance through constructor
    injection (Dependency Inversion) - it never constructs its own
    ``LLMService`` or ``OpenAI`` client. This is what makes every
    concrete agent trivially testable: a test supplies an ``LLMService``
    built with a mocked OpenAI client (see ``app.llm.llm_service``),
    and no agent code changes are needed to support that.

    ``execute()`` is intentionally not itself abstract - it is the fixed
    algorithm skeleton (Template Method pattern). Making the *steps*
    (``_build_prompt``, and optionally ``_validate_input`` /
    ``_build_output``) the extension points, rather than the whole
    method, is what keeps every agent's execution behavior (timing,
    error translation, typed result assembly) consistent without
    duplicating that logic in seven separate classes.
"""

import logging
import time
from abc import ABC, abstractmethod

from app.agents.exceptions import AgentExecutionError, AgentValidationError
from app.agents.models import (
    AgentExecutionResult,
    AgentInput,
    AgentMetadata,
    AgentOutput,
)
from app.llm.exceptions import InvalidPromptError, LLMError
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage, LLMRequest, LLMResponse

logger = logging.getLogger("codepilot.agents.base_agent")


class BaseAgent(ABC):
    """Common interface and execution lifecycle for every SDLC agent.

    Attributes:
        metadata: Identity metadata for this agent instance (type, name,
            description, version).
    """

    def __init__(self, llm_service: LLMService, metadata: AgentMetadata) -> None:
        """Initialize the agent with its LLM collaborator and identity.

        Args:
            llm_service: The LLM service this agent uses to generate its
                output. Injected rather than constructed internally, so
                every agent can be tested with a mocked service and so
                a single shared ``LLMService`` instance can be reused
                across many agents in a future orchestration layer.
            metadata: Identity metadata describing this agent, supplied
                by the concrete subclass's constructor.
        """
        self._llm_service = llm_service
        self.metadata = metadata

    def execute(self, agent_input: AgentInput) -> AgentExecutionResult:
        """Run this agent's full execution lifecycle for a given input.

        Fixed sequence of steps:
            1. Validate the input (``_validate_input``).
            2. Build the prompt (``_build_prompt``, agent-specific).
            3. Invoke the LLM via the injected ``LLMService``.
            4. Build the typed output (``_build_output``).
            5. Assemble and return a complete ``AgentExecutionResult``.

        Args:
            agent_input: The structured input for this execution.

        Returns:
            AgentExecutionResult: The complete, typed record of this
            execution, including output, token usage, and timing.

        Raises:
            AgentValidationError: If input validation fails, or if
                prompt construction fails due to invalid/insufficient
                context (translated from ``InvalidPromptError``).
            AgentExecutionError: If the underlying LLM invocation fails
                (translated from any ``LLMError`` subtype).
        """
        start_time = time.perf_counter()

        self._validate_input(agent_input)

        try:
            messages = self._build_prompt(agent_input)
        except InvalidPromptError as exc:
            logger.warning(
                "base_agent.prompt_construction_failed",
                extra={"agent_type": self.metadata.agent_type.value},
            )
            raise AgentValidationError(
                f"{self.metadata.agent_name} failed to build a valid prompt: {exc}"
            ) from exc

        request = LLMRequest(
            messages=messages,
            model=agent_input.model_override,
            temperature=agent_input.temperature_override,
        )

        try:
            response = self._llm_service.complete(request)
        except LLMError as exc:
            logger.error(
                "base_agent.llm_invocation_failed",
                extra={"agent_type": self.metadata.agent_type.value, "error": str(exc)},
            )
            raise AgentExecutionError(
                f"{self.metadata.agent_name} failed during LLM invocation: {exc}"
            ) from exc

        output = self._build_output(response, agent_input)
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "base_agent.execution_succeeded",
            extra={
                "agent_type": self.metadata.agent_type.value,
                "execution_time_ms": round(execution_time_ms, 2),
                "total_tokens": response.usage.total_tokens,
            },
        )

        return AgentExecutionResult(
            agent_metadata=self.metadata,
            agent_input=agent_input,
            output=output,
            token_usage=response.usage,
            execution_time_ms=execution_time_ms,
        )

    def _validate_input(self, agent_input: AgentInput) -> None:
        """Validate agent input before any prompt construction or LLM call.

        The default implementation checks only that a project ID is
        present on the context, since ``AgentInput`` and ``AgentContext``
        already enforce non-empty task descriptions and project IDs at
        the Pydantic level. Concrete agents may override this method to
        add agent-specific validation (e.g., requiring
        ``document_context`` to be present for agents that cannot
        operate without grounding material).

        Args:
            agent_input: The input to validate.

        Raises:
            AgentValidationError: If validation fails.
        """
        if not agent_input.context.project_id.strip():
            raise AgentValidationError("AgentContext.project_id must not be empty.")

    @abstractmethod
    def _build_prompt(self, agent_input: AgentInput) -> list[ChatMessage]:
        """Build this agent's prompt for a given execution.

        Every concrete agent must implement this method, defining its
        own role description, task instructions, and how it weaves
        ``agent_input.context`` into the conversation sent to the LLM.

        Args:
            agent_input: The structured input for this execution.

        Returns:
            list[ChatMessage]: The full conversation to send to the LLM.

        Raises:
            InvalidPromptError: If the input does not contain enough
                information to build a valid prompt (caught and
                translated to ``AgentValidationError`` by ``execute``).
        """
        raise NotImplementedError

    def _build_output(self, response: LLMResponse, agent_input: AgentInput) -> AgentOutput:
        """Build this agent's typed output from a raw LLM response.

        The default implementation wraps the response content directly,
        alongside generation metadata (model and finish reason).
        Concrete agents may override this method to post-process the
        response into a more specific shape (e.g., parsing a structured
        section out of the content) without needing to duplicate the
        rest of the execution lifecycle.

        Args:
            response: The parsed LLM response for this execution.
            agent_input: The input that produced this response,
                available for context if a subclass needs it.

        Returns:
            AgentOutput: The agent's structured output.
        """
        return AgentOutput(
            content=response.content,
            metadata={
                "model": response.model,
                "finish_reason": response.finish_reason,
            },
        )