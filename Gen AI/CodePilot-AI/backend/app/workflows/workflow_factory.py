"""
Workflow factory.

``WorkflowFactory`` is the only place in this package that decides
*which* nodes exist in a given workflow and *how* they're wired
together. It composes ``WorkflowBuilder`` (graph construction),
``nodes.py`` (node factories bound to injected services), and
``conditional_edges.py`` (routing decisions) into four ready-to-invoke,
compiled graphs.

Design decision:
    Every workflow variant shares the same underlying node factories and
    the same ``GraphState`` schema - a "requirements only" workflow is
    not a different pipeline reimplemented from scratch, it is a
    smaller subgraph of the exact same building blocks used by the full
    SDLC workflow. This is what "Factory only" means in practice: this
    class assembles graphs, it does not know how to ingest a document,
    retrieve a chunk, or dispatch an agent - all of that remains in
    ``nodes.py`` and the packages it delegates to.

    The full SDLC workflow's linear ordering is driven by
    ``conditional_edges.next_agent``, which encodes the canonical
    SDLC phase sequence. The smaller, partial workflows use their own
    lightweight linear routers instead of ``next_agent``, since
    ``next_agent`` always advances along the *full* sequence - reusing
    it in a graph that only registers a subset of that sequence's nodes
    would route to an unregistered node name. Keeping this distinction
    explicit is more honest than papering over it with a shared router
    that only works for one specific graph shape.
"""

import logging
from collections.abc import Callable

from langgraph.graph.state import CompiledStateGraph

from app.application.agent_router import AgentRouter
from app.application.ingestion_service import IngestionService
from app.persistence.repositories import WorkflowRunRepository, ArtifactRepository
from app.rag.retriever import RetrieverService
from app.workflows.conditional_edges import (
    has_documents,
    needs_review,
    next_agent,
    should_continue,
)
from app.workflows.nodes import (
    architecture_agent_node,
    coding_agent_node,
    documentation_agent_node,
    ingest_documents_node,
    planning_agent_node,
    requirements_agent_node,
    retrieve_context_node,
    review_agent_node,
    save_output_node,
    testing_agent_node,
)
from app.workflows.state import GraphState
from app.workflows.workflow_builder import WorkflowBuilder

logger = logging.getLogger("codepilot.workflows.workflow_factory")


def _route_or_finish(next_node_name: str) -> Callable[[GraphState], str]:
    """Build a linear router that finishes early if the workflow has errors.

    Shared plumbing helper used by the partial workflow factories below.
    Not a business rule of its own - purely a small composition over
    ``should_continue`` so every partial workflow doesn't need to
    hand-roll the same three-line closure.

    Args:
        next_node_name: The node to route to when the workflow should
            continue normally.

    Returns:
        Callable[[GraphState], str]: A router function returning
        ``next_node_name`` when ``should_continue`` is ``True``, or
        ``"save_output"`` otherwise.
    """

    def _router(state: GraphState) -> str:
        return next_node_name if should_continue(state) else "save_output"

    return _router


def _full_sequence_router(state: GraphState) -> str:
    """Route using the canonical full-SDLC phase sequence, unless blocked.

    Args:
        state: The current workflow state.

    Returns:
        str: ``"save_output"`` if the workflow should not continue
        (errors present), otherwise the next node per
        ``conditional_edges.next_agent``.
    """
    if not should_continue(state):
        return "save_output"
    return next_agent(state)


def _post_documentation_router(state: GraphState) -> str:
    """Route after the documentation phase, branching on whether review is warranted.

    This is the full SDLC workflow's one genuine branch point: rather
    than unconditionally following documentation with review (as the
    default phase sequence would), this checks ``needs_review`` so a
    workflow run that never produced code (e.g., a documentation-only
    task fed through the full graph) skips a pointless review pass.

    Args:
        state: The current workflow state.

    Returns:
        str: ``"save_output"`` if the workflow should not continue,
        ``"review_agent"`` if review is warranted, otherwise
        ``"save_output"``.
    """
    if not should_continue(state):
        return "save_output"
    return "review_agent" if needs_review(state) else "save_output"


def _entry_router(state: GraphState) -> str:
    """Route the graph's entry point based on whether documents were supplied.

    Args:
        state: The workflow's initial state.

    Returns:
        str: ``"ingest_documents"`` if ``has_documents`` is ``True``,
        otherwise ``"retrieve_context"`` (skipping ingestion entirely
        when there is nothing to ingest).
    """
    return "ingest_documents" if has_documents(state) else "retrieve_context"


class WorkflowFactory:
    """Assembles configured, compiled LangGraph workflows from existing services."""

    def __init__(
        self,
        ingestion_service: IngestionService,
        retriever: RetrieverService,
        agent_router: AgentRouter,
        workflow_run_repository: WorkflowRunRepository,
        artifact_repository: ArtifactRepository,
    ) -> None:
        """Initialize the factory with the services and repositories every workflow will use.

        Args:
            ingestion_service: Injected into ``ingest_documents_node``.
            retriever: Injected into ``retrieve_context_node``.
            agent_router: Injected into every agent node.
            workflow_run_repository: SQLite repository to track runs.
            artifact_repository: SQLite repository to persist artifacts.
        """
        self._ingestion_service = ingestion_service
        self._retriever = retriever
        self._agent_router = agent_router
        self._workflow_run_repository = workflow_run_repository
        self._artifact_repository = artifact_repository

    def create_full_sdlc_workflow(self) -> CompiledStateGraph:
        """Build the complete, seven-agent SDLC workflow.

        Sequence: ingest_documents (conditionally skipped) ->
        retrieve_context -> requirements_agent -> architecture_agent ->
        planning_agent -> coding_agent -> testing_agent ->
        documentation_agent -> (conditionally) review_agent ->
        save_output.

        Returns:
            CompiledStateGraph: The compiled full SDLC workflow.
        """
        builder = (
            WorkflowBuilder()
            .add_node("ingest_documents", ingest_documents_node(self._ingestion_service, self._workflow_run_repository))
            .add_node("retrieve_context", retrieve_context_node(self._retriever, self._workflow_run_repository))
            .add_node("requirements_agent", requirements_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("architecture_agent", architecture_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("planning_agent", planning_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("coding_agent", coding_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("testing_agent", testing_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("documentation_agent", documentation_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("review_agent", review_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("save_output", save_output_node(self._workflow_run_repository))
            .set_conditional_entry_point(_entry_router)
            .add_conditional_edges("ingest_documents", _full_sequence_router)
            .add_conditional_edges("retrieve_context", _full_sequence_router)
            .add_conditional_edges("requirements_agent", _full_sequence_router)
            .add_conditional_edges("architecture_agent", _full_sequence_router)
            .add_conditional_edges("planning_agent", _full_sequence_router)
            .add_conditional_edges("coding_agent", _full_sequence_router)
            .add_conditional_edges("testing_agent", _full_sequence_router)
            .add_conditional_edges("documentation_agent", _post_documentation_router)
            .add_edge("review_agent", "save_output")
            .set_finish_point("save_output")
        )

        logger.info("workflow_factory.building_full_sdlc_workflow")
        return builder.compile()

    def create_requirements_only(self) -> CompiledStateGraph:
        """Build a minimal workflow that only extracts requirements.

        Sequence: ingest_documents (conditionally skipped) ->
        retrieve_context -> requirements_agent -> save_output.

        Returns:
            CompiledStateGraph: The compiled requirements-only workflow.
        """
        builder = (
            WorkflowBuilder()
            .add_node("ingest_documents", ingest_documents_node(self._ingestion_service, self._workflow_run_repository))
            .add_node("retrieve_context", retrieve_context_node(self._retriever, self._workflow_run_repository))
            .add_node("requirements_agent", requirements_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("save_output", save_output_node(self._workflow_run_repository))
            .set_conditional_entry_point(_entry_router)
            .add_conditional_edges("ingest_documents", _route_or_finish("retrieve_context"))
            .add_conditional_edges("retrieve_context", _route_or_finish("requirements_agent"))
            .add_conditional_edges("requirements_agent", _route_or_finish("save_output"))
            .set_finish_point("save_output")
        )

        logger.info("workflow_factory.building_requirements_only_workflow")
        return builder.compile()

    def create_testing_workflow(self) -> CompiledStateGraph:
        """Build a workflow that designs tests grounded in existing context.

        Assumes requirements/code already exist as ingested documents or
        prior conversation context - this workflow only retrieves and
        dispatches the Testing Agent.

        Sequence: retrieve_context -> testing_agent -> save_output.

        Returns:
            CompiledStateGraph: The compiled testing workflow.
        """
        builder = (
            WorkflowBuilder()
            .add_node("retrieve_context", retrieve_context_node(self._retriever, self._workflow_run_repository))
            .add_node("testing_agent", testing_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("save_output", save_output_node(self._workflow_run_repository))
            .set_entry_point("retrieve_context")
            .add_conditional_edges("retrieve_context", _route_or_finish("testing_agent"))
            .add_conditional_edges("testing_agent", _route_or_finish("save_output"))
            .set_finish_point("save_output")
        )

        logger.info("workflow_factory.building_testing_workflow")
        return builder.compile()

    def create_review_workflow(self) -> CompiledStateGraph:
        """Build a workflow that reviews an existing artifact.

        Assumes the artifact to review already exists as ingested
        documents or prior conversation context - this workflow only
        retrieves and dispatches the Review Agent.

        Sequence: retrieve_context -> review_agent -> save_output.

        Returns:
            CompiledStateGraph: The compiled review workflow.
        """
        builder = (
            WorkflowBuilder()
            .add_node("retrieve_context", retrieve_context_node(self._retriever, self._workflow_run_repository))
            .add_node("review_agent", review_agent_node(self._agent_router, self._workflow_run_repository, self._artifact_repository))
            .add_node("save_output", save_output_node(self._workflow_run_repository))
            .set_entry_point("retrieve_context")
            .add_conditional_edges("retrieve_context", _route_or_finish("review_agent"))
            .add_conditional_edges("review_agent", _route_or_finish("save_output"))
            .set_finish_point("save_output")
        )

        logger.info("workflow_factory.building_review_workflow")
        return builder.compile()