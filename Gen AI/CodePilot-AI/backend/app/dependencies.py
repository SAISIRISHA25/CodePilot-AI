"""Shared FastAPI dependency providers.

This module is the composition seam between the FastAPI interface layer
and the rest of the application. Every dependency the API needs -
configuration, the current request's correlation ID, repositories,
RAG services, LLM services, workflow services, and agent routing - is
provided here as a callable usable with FastAPI's ``Depends()``.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from app.application.agent_router import AgentRouter
from app.application.ingestion_service import IngestionService
from app.application.project_service import ProjectService
from app.application.query_service import QueryService
from app.core.config import get_settings
from app.core.settings import Settings
from app.llm.llm_service import LLMService
from app.persistence.repositories import (
    DocumentRepository,
    WorkflowRunRepository,
    ArtifactRepository,
)
from app.rag.document_loader import DocumentLoaderService
from app.rag.embedding_service import EmbeddingService
from app.rag.retriever import RetrieverService
from app.rag.text_splitter import TextSplitterService
from app.rag.vector_store import VectorStoreService
from app.workflows.executor import WorkflowExecutor
from app.workflows.workflow_factory import WorkflowFactory

# --------------------------------------------------------------------------
# Configuration dependency
# --------------------------------------------------------------------------
# Re-exported as a typed Annotated alias so route handlers can write
# `settings: SettingsDependency` instead of repeating `Depends(get_settings)`
# everywhere. `get_settings` itself is cached (see core.config), so this
# dependency is effectively free after the first call.
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def get_request_id(request: Request) -> str:
    """Retrieve the current request's correlation ID.

    The correlation ID is attached to ``request.state`` by
    ``RequestIDLoggingMiddleware`` earlier in the middleware chain. This
    dependency lets any route handler access it (e.g., to embed it in a
    response body) without coupling the handler to the middleware
    implementation itself.

    Args:
        request: The incoming FastAPI/Starlette request.

    Returns:
        str: The request's unique correlation/request ID.
    """
    # Fall back defensively in case this dependency is ever used outside
    # a request that passed through the logging middleware (e.g., tests).
    return getattr(request.state, "request_id", "unknown")


RequestIdDependency = Annotated[str, Depends(get_request_id)]
# --------------------------------------------------------------------------
# Future infrastructure dependency placeholders
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# The following functions are intentionally NOT implemented yet. They are
# declared now to reserve the dependency-injection seam so that later
# modules (persistence, vector store, LLM provider) plug in without any
# router-level changes. Each will be implemented in its corresponding
# infrastructure module and will return a concrete instance satisfying a
# domain-defined interface.


@lru_cache(maxsize=1)
def get_document_repository() -> DocumentRepository:
    """Provide a SQLite-backed document repository."""
    return DocumentRepository()


@lru_cache(maxsize=1)
def get_workflow_run_repository() -> WorkflowRunRepository:
    """Provide a SQLite-backed workflow run repository."""
    return WorkflowRunRepository()


@lru_cache(maxsize=1)
def get_artifact_repository() -> ArtifactRepository:
    """Provide a SQLite-backed artifact repository."""
    return ArtifactRepository()


@lru_cache(maxsize=1)
def get_project_service() -> ProjectService:
    """Provide the project application service."""
    return ProjectService()


@lru_cache(maxsize=1)
def get_query_service() -> QueryService:
    """Provide the query application service."""
    return QueryService(get_retriever(), get_llm_gateway())


@lru_cache(maxsize=1)
def get_llm_gateway() -> LLMService:
    """Provide the shared OpenAI-backed LLM service."""
    return LLMService()


@lru_cache(maxsize=1)
def get_vector_store_gateway() -> VectorStoreService:
    """Provide the ChromaDB-backed vector store service."""
    return VectorStoreService(embedding_service=get_embedding_service())


@lru_cache(maxsize=1)
def get_document_loader() -> DocumentLoaderService:
    """Provide the document loader service."""
    return DocumentLoaderService()


@lru_cache(maxsize=1)
def get_text_splitter() -> TextSplitterService:
    """Provide the text splitter service."""
    return TextSplitterService()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Provide the embedding service."""
    return EmbeddingService()


@lru_cache(maxsize=1)
def get_retriever() -> RetrieverService:
    """Provide the retrieval service."""
    return RetrieverService(get_vector_store_gateway())


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    """Provide the document ingestion use case."""
    return IngestionService(
        document_loader=get_document_loader(),
        text_splitter=get_text_splitter(),
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store_gateway(),
    )


@lru_cache(maxsize=1)
def get_agent_router() -> AgentRouter:
    """Provide the agent router with the shared LLM service."""
    return AgentRouter(get_llm_gateway())


@lru_cache(maxsize=1)
def get_workflow_factory() -> WorkflowFactory:
    """Provide the workflow factory configured with application services."""
    return WorkflowFactory(
        ingestion_service=get_ingestion_service(),
        retriever=get_retriever(),
        agent_router=get_agent_router(),
        workflow_run_repository=get_workflow_run_repository(),
        artifact_repository=get_artifact_repository(),
    )


@lru_cache(maxsize=1)
def get_workflow_executor() -> WorkflowExecutor:
    """Provide the workflow executor."""
    return WorkflowExecutor()


# Service dependencies annotated types
ProjectServiceDependency = Annotated[ProjectService, Depends(get_project_service)]
DocumentRepositoryDependency = Annotated[DocumentRepository, Depends(get_document_repository)]
IngestionServiceDependency = Annotated[IngestionService, Depends(get_ingestion_service)]
AgentRouterDependency = Annotated[AgentRouter, Depends(get_agent_router)]
QueryServiceDependency = Annotated[QueryService, Depends(get_query_service)]
WorkflowRunRepositoryDependency = Annotated[WorkflowRunRepository, Depends(get_workflow_run_repository)]
ArtifactRepositoryDependency = Annotated[ArtifactRepository, Depends(get_artifact_repository)]