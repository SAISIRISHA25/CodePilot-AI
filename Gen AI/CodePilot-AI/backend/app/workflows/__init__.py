"""
Workflows package for CodePilot AI.

Provides LangGraph-based orchestration over the ``rag``, ``llm``,
``agents``, and ``application`` packages, without implementing any of
their business logic itself:

    GraphState        - the single immutable state model threaded
                         through every workflow node.
    nodes             - one factory function per workflow step, each
                         delegating to an existing application/rag
                         service.
    conditional_edges - pure routing/decision functions over
                         ``GraphState``.
    WorkflowBuilder    - a thin, fluent wrapper around LangGraph's
                         ``StateGraph``.
    WorkflowFactory    - assembles four configured, compiled workflows
                         from the building blocks above.

This package MAY import ``application``, ``agents``, ``rag``, and
``llm``. None of those packages import anything from this package - the
dependency direction is strictly one-way, with orchestration as the
outermost layer.

Typical usage (illustrative only - constructing the underlying
application services from real settings is the responsibility of a
future dependency-injection/wiring module):

    factory = WorkflowFactory(
        ingestion_service=ingestion_service,
        retriever=retriever,
        agent_router=agent_router,
    )
    workflow = factory.create_full_sdlc_workflow()
    final_state = workflow.invoke(
        GraphState(project_id="proj-123", user_prompt="Build a login feature.")
    )
"""

from app.workflows.conditional_edges import (
    has_documents,
    needs_review,
    next_agent,
    should_continue,
    should_finish,
    should_retry,
)
from app.workflows.exceptions import (
    WorkflowCompilationError,
    WorkflowError,
    WorkflowExecutionError,
    WorkflowStateError,
)
from app.workflows.state import (
    GraphState,
    RetrievedContextItem,
    UploadedDocument,
    WorkflowHistoryEntry,
    WorkflowPhase,
)
from app.workflows.workflow_builder import WorkflowBuilder
from app.workflows.workflow_factory import WorkflowFactory

__all__ = [
    # State
    "GraphState",
    "WorkflowPhase",
    "UploadedDocument",
    "RetrievedContextItem",
    "WorkflowHistoryEntry",
    # Builder & factory
    "WorkflowBuilder",
    "WorkflowFactory",
    # Routing functions
    "should_continue",
    "should_retry",
    "should_finish",
    "next_agent",
    "has_documents",
    "needs_review",
    # Exceptions
    "WorkflowError",
    "WorkflowCompilationError",
    "WorkflowExecutionError",
    "WorkflowStateError",
]