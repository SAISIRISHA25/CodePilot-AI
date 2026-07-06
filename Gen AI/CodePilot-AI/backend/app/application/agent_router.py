"""
Agent dispatch use case.

``AgentRouter`` maps an ``AgentType`` to its concrete ``BaseAgent``
implementation and dispatches a single execution to it. This is
deliberately NOT a workflow engine - it has no concept of sequencing,
handoffs between agents, or conditional branching. It answers exactly
one question: "given this agent type and this input, produce this
agent's output." Composing multiple dispatches into a multi-step SDLC
pipeline is the explicit responsibility of the future LangGraph
orchestration module.

Design decision:
    Agents are registered in a plain ``dict[AgentType, BaseAgent]``
    built once in the constructor (a Registry/Strategy pattern). Adding
    a new agent type in the future means adding one entry to this dict
    and importing one new class - no other method in this class needs
    to change (Open/Closed Principle). Every concrete agent still
    receives the same single, shared ``LLMService`` instance, avoiding
    redundant client construction.
"""

import logging

from app.agents.architecture_agent import ArchitectureAgent
from app.agents.base_agent import BaseAgent
from app.agents.coding_agent import CodingAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.exceptions import AgentError
from app.agents.models import AgentContext
from app.agents.models import AgentInput as AgentExecutionInput
from app.agents.models import AgentType
from app.agents.planning_agent import PlanningAgent
from app.agents.requirements_agent import RequirementsAgent
from app.agents.review_agent import ReviewAgent
from app.agents.testing_agent import TestingAgent
from app.application.exceptions import AgentRoutingError
from app.application.models import AgentRequest, AgentResponse
from app.llm.llm_service import LLMService

logger = logging.getLogger("codepilot.application.agent_router")


class AgentRouter:
    """Dispatches a single agent execution to the correct SDLC agent."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize the router and eagerly construct every registered agent.

        Args:
            llm_service: The shared LLM service injected into every
                registered agent. Each agent is lightweight (it holds
                only this reference and its own metadata), so
                constructing all seven up front is inexpensive and
                means dispatch never pays agent-construction cost.
        """
        self._llm_service = llm_service
        self._agents: dict[AgentType, BaseAgent] = {
            AgentType.REQUIREMENTS: RequirementsAgent(llm_service=llm_service),
            AgentType.ARCHITECTURE: ArchitectureAgent(llm_service=llm_service),
            AgentType.PLANNING: PlanningAgent(llm_service=llm_service),
            AgentType.CODING: CodingAgent(llm_service=llm_service),
            AgentType.TESTING: TestingAgent(llm_service=llm_service),
            AgentType.DOCUMENTATION: DocumentationAgent(llm_service=llm_service),
            AgentType.REVIEW: ReviewAgent(llm_service=llm_service),
        }

    def dispatch(self, request: AgentRequest) -> AgentResponse:
        """Dispatch a single execution to the agent identified by the request.

        Args:
            request: The structured agent dispatch request.

        Returns:
            AgentResponse: The dispatched agent's typed result.

        Raises:
            AgentRoutingError: If ``request.agent_type`` has no
                registered agent, or if the dispatched agent's
                execution fails for any reason.
        """
        agent = self._agents.get(request.agent_type)
        if agent is None:
            # Defensive: AgentType is a closed enum and every member is
            # registered above, so this branch should be unreachable in
            # practice. It exists so a future addition to AgentType that
            # forgets to register a corresponding agent fails loudly and
            # specifically, rather than with a raw KeyError.
            raise AgentRoutingError(
                f"No agent is registered for agent type '{request.agent_type.value}'."
            )

        agent_input = AgentExecutionInput(
            task_description=request.task_description,
            context=AgentContext(
                project_id=request.project_id,
                document_context=request.document_context,
                additional_context=request.additional_context,
            ),
            model_override=request.model_override,
            temperature_override=request.temperature_override,
        )

        try:
            result = agent.execute(agent_input)
        except AgentError as exc:
            logger.error(
                "agent_router.dispatch_failed",
                extra={"agent_type": request.agent_type.value, "error": str(exc)},
            )
            raise AgentRoutingError(
                f"Dispatch to '{request.agent_type.value}' failed: {exc}"
            ) from exc

        logger.info(
            "agent_router.dispatch_succeeded",
            extra={
                "agent_type": request.agent_type.value,
                "execution_time_ms": round(result.execution_time_ms, 2),
            },
        )

        return AgentResponse(
            agent_type=result.agent_metadata.agent_type,
            agent_name=result.agent_metadata.agent_name,
            content=result.output.content,
            token_usage=result.token_usage,
            execution_time_ms=result.execution_time_ms,
        )