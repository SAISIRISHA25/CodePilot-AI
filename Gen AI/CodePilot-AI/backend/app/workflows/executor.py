"""Simple workflow execution wrapper for compiled LangGraph graphs."""

from __future__ import annotations

from langgraph.graph.state import CompiledStateGraph

from app.workflows.exceptions import WorkflowExecutionError
from app.workflows.state import GraphState


class WorkflowExecutor:
    """Executes compiled workflows against a workflow state."""

    def execute(self, workflow: CompiledStateGraph, state: GraphState) -> GraphState:
        try:
            result = workflow.invoke(state)
        except Exception as exc:  # pragma: no cover - defensive
            raise WorkflowExecutionError(f"Failed to execute workflow: {exc}") from exc

        if isinstance(result, GraphState):
            return result

        if isinstance(result, dict):
            try:
                return GraphState.model_validate(result)
            except Exception as exc:  # pragma: no cover - defensive
                raise WorkflowExecutionError(
                    "Workflow execution returned a mapping that could not be validated as GraphState"
                ) from exc

        if hasattr(result, "model_dump"):
            try:
                return GraphState.model_validate(result.model_dump())
            except Exception as exc:  # pragma: no cover - defensive
                raise WorkflowExecutionError(
                    "Workflow execution returned a model that could not be validated as GraphState"
                ) from exc

        raise WorkflowExecutionError("Workflow execution did not return a GraphState")
