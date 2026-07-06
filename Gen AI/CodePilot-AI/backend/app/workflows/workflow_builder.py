"""
Workflow graph builder.

``WorkflowBuilder`` is a thin, fluent wrapper around LangGraph's
``StateGraph``. It adds exactly two things beyond what ``StateGraph``
already provides: a chainable API for readability, and centralized
exception translation (LangGraph's own compilation failures become
``WorkflowCompilationError``). It contains no orchestration policy of
its own - which nodes exist, how they're wired, and which workflows are
assembled from them is entirely the responsibility of
``workflow_factory.py``, which uses this builder as a tool.

Design decision:
    Every method returns ``self``, allowing
    ``WorkflowBuilder(...).add_node(...).add_node(...).add_edge(...).compile()``
    - a builder pattern that makes the shape of a graph readable
    top-to-bottom at its construction site in ``workflow_factory.py``,
    rather than as a sequence of statements on a bare ``StateGraph``.
"""

import logging
from collections.abc import Callable

from langgraph.graph import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from app.workflows.exceptions import WorkflowCompilationError
from app.workflows.state import GraphState

logger = logging.getLogger("codepilot.workflows.workflow_builder")

# Re-exported so callers of this module (workflow_factory.py) can build
# routing path maps without importing langgraph directly themselves.
START_NODE = START
END_NODE = END


class WorkflowBuilder:
    """Fluent builder around a LangGraph ``StateGraph`` keyed on ``GraphState``."""

    def __init__(self) -> None:
        """Initialize a new, empty graph builder."""
        self._graph: StateGraph = StateGraph(GraphState)

    def add_node(
        self, name: str, node_fn: Callable[[GraphState], GraphState]
    ) -> "WorkflowBuilder":
        """Register a node in the graph.

        Args:
            name: The unique name this node will be referenced by in
                edges and conditional routing.
            node_fn: The node function, typically produced by one of
                the factory functions in ``workflows.nodes``.

        Returns:
            WorkflowBuilder: ``self``, for chaining.
        """
        self._graph.add_node(name, node_fn)
        return self

    def add_edge(self, start: str, end: str) -> "WorkflowBuilder":
        """Register a fixed, unconditional edge between two nodes.

        Args:
            start: The source node name (or ``START_NODE``).
            end: The destination node name (or ``END_NODE``).

        Returns:
            WorkflowBuilder: ``self``, for chaining.
        """
        self._graph.add_edge(start, end)
        return self

    def add_conditional_edges(
        self,
        source: str,
        router: Callable[[GraphState], str],
        path_map: dict[str, str] | None = None,
    ) -> "WorkflowBuilder":
        """Register a conditional edge, routed by a function from ``conditional_edges``.

        Args:
            source: The node name this routing decision is made after.
            router: A routing function (e.g.,
                ``app.workflows.conditional_edges.next_agent``) that
                inspects ``GraphState`` and returns the next node name.
            path_map: Optional explicit mapping restricting/validating
                which node names ``router`` is allowed to return. When
                omitted, LangGraph infers reachable targets dynamically.

        Returns:
            WorkflowBuilder: ``self``, for chaining.
        """
        if path_map is not None:
            self._graph.add_conditional_edges(source, router, path_map)
        else:
            self._graph.add_conditional_edges(source, router)
        return self

    def set_entry_point(self, name: str) -> "WorkflowBuilder":
        """Mark a node as the graph's entry point.

        Args:
            name: The node name execution should begin at.

        Returns:
            WorkflowBuilder: ``self``, for chaining.
        """
        self._graph.add_edge(START_NODE, name)
        return self

    def set_conditional_entry_point(
        self,
        router: Callable[[GraphState], str],
        path_map: dict[str, str] | None = None,
    ) -> "WorkflowBuilder":
        """Route to one of several possible first nodes based on initial state.

        Args:
            router: A routing function inspecting the workflow's initial
                ``GraphState`` and returning the name of the node
                execution should begin at.
            path_map: Optional explicit mapping restricting/validating
                which node names ``router`` is allowed to return.

        Returns:
            WorkflowBuilder: ``self``, for chaining.
        """
        if path_map is not None:
            self._graph.set_conditional_entry_point(router, path_map)
        else:
            self._graph.set_conditional_entry_point(router)
        return self

    def set_finish_point(self, name: str) -> "WorkflowBuilder":
        """Mark a node as a graph's finish point.

        Args:
            name: The node name that, once executed, ends the workflow.

        Returns:
            WorkflowBuilder: ``self``, for chaining.
        """
        self._graph.add_edge(name, END_NODE)
        return self

    def compile(self) -> CompiledStateGraph:
        """Compile the constructed graph into an executable workflow.

        Returns:
            CompiledStateGraph: The compiled LangGraph graph, ready for
            ``.invoke(...)``.

        Raises:
            WorkflowCompilationError: If LangGraph rejects the graph
                (e.g., a dangling edge referencing an unregistered node,
                or an unreachable node).
        """
        try:
            compiled = self._graph.compile()
        except Exception as exc:
            logger.exception("workflow_builder.compilation_failed")
            raise WorkflowCompilationError(f"Failed to compile workflow graph: {exc}") from exc

        logger.info("workflow_builder.compilation_succeeded")
        return compiled