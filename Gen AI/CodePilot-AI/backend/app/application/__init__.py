"""
Application Services package for CodePilot AI.

Composes the ``rag``, ``llm``, and ``agents`` packages into three
complete use cases:

    IngestionService  - loads, splits, embeds, and stores a document.
    QueryService      - answers a project-scoped question grounded in
                         retrieved document chunks.
    AgentRouter        - dispatches a single execution to the correct
                         SDLC agent.

This is the outermost layer of business logic before the interface
layer (FastAPI routes, in a later module). It contains no FastAPI code,
no LangGraph orchestration, and no persistence/database code - every
service here is a plain Python class receiving its lower-level
collaborators through constructor injection, composable by a future
dependency-injection wiring module (``app.dependencies``) or a future
LangGraph node.

Typical composition (illustrative only - wiring these together with
real settings-derived collaborators is the responsibility of a future
dependency-injection module):

    ingestion_service = IngestionService(
        document_loader=DocumentLoaderService(),
        text_splitter=TextSplitterService(),
        embedding_service=embedding_service,
        vector_store=VectorStoreService(embedding_service=embedding_service),
    )
    result = ingestion_service.ingest_document(
        project_id="proj-123", file_path="/path/to/brd.pdf",
        filename="brd.pdf", document_type=DocumentType.BUSINESS_REQUIREMENT_DOCUMENT,
    )
"""

from app.application.agent_router import AgentRouter
from app.application.exceptions import (
    AgentRoutingError,
    ApplicationError,
    IngestionServiceError,
    QueryServiceError,
)
from app.application.ingestion_service import IngestionService
from app.application.models import (
    AgentRequest,
    AgentResponse,
    IngestionResult,
    QueryRequest,
    QueryResponse,
    QuerySource,
)
from app.application.query_service import QueryService

__all__ = [
    # Services
    "IngestionService",
    "QueryService",
    "AgentRouter",
    # Models
    "IngestionResult",
    "QueryRequest",
    "QueryResponse",
    "QuerySource",
    "AgentRequest",
    "AgentResponse",
    # Exceptions
    "ApplicationError",
    "IngestionServiceError",
    "QueryServiceError",
    "AgentRoutingError",
]