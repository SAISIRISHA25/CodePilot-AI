from __future__ import annotations

import tempfile
from pathlib import Path

from app.dependencies import (
    get_document_repository,
    get_llm_gateway,
    get_vector_store_gateway,
    get_workflow_factory,
    get_workflow_executor,
)
from app.persistence.repositories import DocumentRepository
from app.workflows.executor import WorkflowExecutor
from app.workflows.state import GraphState
from app.workflows.workflow_builder import WorkflowBuilder


def test_document_repository_round_trip(tmp_path: Path) -> None:
    repo = DocumentRepository(database_path=str(tmp_path / "test.db"))

    created = repo.create_document(
        project_id="proj-1",
        filename="spec.pdf",
        document_type="business_requirement_document",
        file_path="/tmp/spec.pdf",
    )

    fetched = repo.get_document(created["id"])
    assert fetched is not None
    assert fetched["filename"] == "spec.pdf"
    assert fetched["project_id"] == "proj-1"

    updated = repo.update_document(created["id"], filename="spec-v2.pdf")
    assert updated is not None
    assert updated["filename"] == "spec-v2.pdf"

    listed = repo.list_documents(project_id="proj-1")
    assert len(listed) == 1


def test_dependency_providers_return_real_services() -> None:
    repository = get_document_repository()
    llm_gateway = get_llm_gateway()
    vector_store = get_vector_store_gateway()
    workflow_factory = get_workflow_factory()
    workflow_executor = get_workflow_executor()

    assert isinstance(repository, DocumentRepository)
    assert llm_gateway is not None
    assert vector_store is not None
    assert workflow_factory is not None
    assert isinstance(workflow_executor, WorkflowExecutor)


def test_workflow_executor_runs_simple_graph() -> None:
    def add_marker(state: GraphState) -> GraphState:
        return state.model_copy(update={"metadata": {"marker": "done"}})

    builder = (
        WorkflowBuilder()
        .add_node("start", add_marker)
        .set_entry_point("start")
        .set_finish_point("start")
    )

    executor = WorkflowExecutor()
    result = executor.execute(builder.compile(), GraphState(project_id="proj-1"))

    assert result.metadata["marker"] == "done"


def test_deterministic_local_embeddings() -> None:
    from app.rag.embedding_service import DeterministicLocalEmbeddings
    emb = DeterministicLocalEmbeddings()
    v1 = emb.embed_query("test query")
    v2 = emb.embed_query("test query")
    v3 = emb.embed_query("different query")
    
    assert len(v1) == 1536
    assert v1 == v2
    assert v1 != v3
    
    docs = emb.embed_documents(["doc1", "doc2"])
    assert len(docs) == 2
    assert len(docs[0]) == 1536
