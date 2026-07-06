"""
Exception hierarchy for the Workflows (LangGraph orchestration) package.

Every failure mode specific to graph construction, compilation, and
execution is represented by a dedicated exception class rooted at
``WorkflowError``. This package translates failures from LangGraph
itself, and from the application/agents/rag/llm services it
coordinates, into this package's own exception vocabulary at the
orchestration boundary.

Design decision:
    Kept separate from ``app.application.exceptions``,
    ``app.agents.exceptions``, ``app.rag.exceptions``, and
    ``app.llm.exceptions`` for the same reason those packages each keep
    their own hierarchy: this package owns the failure vocabulary for
    its own concern (orchestration), and translates - rather than
    re-raises - the failures of the packages it depends on.
"""


class WorkflowError(Exception):
    """Base exception for all errors raised by the Workflows package.

    Catching this exception type catches any failure originating from
    graph construction, compilation, state handling, or execution.
    """


class WorkflowCompilationError(WorkflowError):
    """Raised when a LangGraph ``StateGraph`` fails to compile.

    Covers malformed graphs (e.g., missing nodes referenced by an edge,
    unreachable nodes, missing entry/finish points) surfaced by
    LangGraph's own ``compile()`` call.
    """


class WorkflowExecutionError(WorkflowError):
    """Raised when a compiled workflow fails during execution.

    Wraps any exception raised while invoking a compiled graph,
    including failures propagated up from the underlying application
    services a node delegates to (ingestion, retrieval, or agent
    dispatch failures).
    """


class WorkflowStateError(WorkflowError):
    """Raised when workflow state is invalid or cannot be constructed.

    Covers cases such as attempting to start a workflow with a missing
    required field, or a node receiving state that fails
    ``GraphState`` validation when reconstructed from the graph's
    internal representation.
    """