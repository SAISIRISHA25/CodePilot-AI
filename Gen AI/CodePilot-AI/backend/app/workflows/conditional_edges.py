"""
Conditional edge routing functions.

Every function here answers exactly one routing question about the
current ``GraphState`` and returns either a ``bool`` or the name of the
next node to visit. None of these functions call an LLM, perform vector
search, or invoke any agent - they only inspect fields already present
on ``GraphState`` (``errors``, ``current_phase``, ``generated_outputs``,
``uploaded_documents``) and make a decision. This is what keeps them
independently unit-testable with nothing more than a hand-built
``GraphState`` instance - no mocked services required.

Design decision:
    ``next_agent`` encodes the default linear SDLC ordering
    (requirements -> architecture -> planning -> coding -> testing ->
    documentation -> review -> save_output) as a single ordered list,
    walked by matching ``state.current_phase``. Centralizing the
    sequence here - rather than scattering "what comes after me" logic
    across individual nodes - means the workflow's shape is defined in
    exactly one place, which ``workflow_factory.py`` composes graphs
    around.
"""

from app.core.constants import DEFAULT_AGENT_MAX_RETRIES
from app.workflows.state import GraphState, WorkflowPhase

# The default full SDLC phase ordering used by `next_agent`. Deliberately
# module-level (not embedded in a function body) so both
# `next_agent` and any future test can inspect the exact sequence.
_DEFAULT_PHASE_SEQUENCE: list[WorkflowPhase] = [
    WorkflowPhase.INGESTION,
    WorkflowPhase.RETRIEVAL,
    WorkflowPhase.REQUIREMENTS,
    WorkflowPhase.ARCHITECTURE,
    WorkflowPhase.PLANNING,
    WorkflowPhase.CODING,
    WorkflowPhase.TESTING,
    WorkflowPhase.DOCUMENTATION,
    WorkflowPhase.REVIEW,
    WorkflowPhase.SAVE_OUTPUT,
]

# Maps each phase to the LangGraph node name that performs it, matching
# the node names `workflow_factory.py` registers via `add_node`.
_PHASE_TO_NODE_NAME: dict[WorkflowPhase, str] = {
    WorkflowPhase.INGESTION: "ingest_documents",
    WorkflowPhase.RETRIEVAL: "retrieve_context",
    WorkflowPhase.REQUIREMENTS: "requirements_agent",
    WorkflowPhase.ARCHITECTURE: "architecture_agent",
    WorkflowPhase.PLANNING: "planning_agent",
    WorkflowPhase.CODING: "coding_agent",
    WorkflowPhase.TESTING: "testing_agent",
    WorkflowPhase.DOCUMENTATION: "documentation_agent",
    WorkflowPhase.REVIEW: "review_agent",
    WorkflowPhase.SAVE_OUTPUT: "save_output",
}


def should_continue(state: GraphState) -> bool:
    """Decide whether the workflow should proceed to its next step.

    Args:
        state: The current workflow state.

    Returns:
        bool: ``True`` if no errors have been recorded and the workflow
        has not already finished; ``False`` otherwise.
    """
    if state.current_phase in (WorkflowPhase.COMPLETED, WorkflowPhase.FAILED):
        return False
    return len(state.errors) == 0


def should_retry(state: GraphState) -> bool:
    """Decide whether a failed step should be retried.

    Args:
        state: The current workflow state.

    Returns:
        bool: ``True`` if at least one error has been recorded but the
        number of accumulated errors is still under the configured
        retry threshold (``app.core.constants.DEFAULT_AGENT_MAX_RETRIES``);
        ``False`` once that threshold is reached.
    """
    return 0 < len(state.errors) <= DEFAULT_AGENT_MAX_RETRIES


def should_finish(state: GraphState) -> bool:
    """Decide whether the workflow has reached a terminal state.

    Args:
        state: The current workflow state.

    Returns:
        bool: ``True`` if ``current_phase`` is ``COMPLETED`` or
        ``FAILED``.
    """
    return state.current_phase in (WorkflowPhase.COMPLETED, WorkflowPhase.FAILED)


def has_documents(state: GraphState) -> bool:
    """Decide whether the workflow has any documents available to ingest.

    Args:
        state: The current workflow state.

    Returns:
        bool: ``True`` if ``uploaded_documents`` is non-empty.
    """
    return len(state.uploaded_documents) > 0


def needs_review(state: GraphState) -> bool:
    """Decide whether generated code warrants a review pass.

    Args:
        state: The current workflow state.

    Returns:
        bool: ``True`` if a coding-phase output has been generated and
        no review output exists yet.
    """
    return "coding" in state.generated_outputs and "review" not in state.generated_outputs


def next_agent(state: GraphState) -> str:
    """Determine the next node name in the default SDLC sequence.

    Walks ``_DEFAULT_PHASE_SEQUENCE`` to find the phase immediately
    after ``state.current_phase`` and returns its corresponding node
    name. Intended for use as the routing function passed to
    ``StateGraph.add_conditional_edges``.

    Args:
        state: The current workflow state.

    Returns:
        str: The name of the next node to visit, or ``"save_output"``
        if ``current_phase`` is not found in the sequence (defensive
        fallback that routes toward workflow completion rather than
        raising during graph execution).
    """
    if state.current_phase not in _DEFAULT_PHASE_SEQUENCE:
        return _PHASE_TO_NODE_NAME[WorkflowPhase.SAVE_OUTPUT]

    current_index = _DEFAULT_PHASE_SEQUENCE.index(state.current_phase)
    if current_index + 1 >= len(_DEFAULT_PHASE_SEQUENCE):
        return _PHASE_TO_NODE_NAME[WorkflowPhase.SAVE_OUTPUT]

    next_phase = _DEFAULT_PHASE_SEQUENCE[current_index + 1]
    return _PHASE_TO_NODE_NAME[next_phase]