"""
RAG (Retrieval Augmented Generation) package for CodePilot AI.

Provides reusable, composable services for document ingestion and
retrieval:

    DocumentLoaderService  - loads PDF/DOCX/TXT files into LangChain
                              Document objects.
    TextSplitterService    - splits documents into metadata-tagged
                              chunks using RecursiveCharacterTextSplitter.
    EmbeddingService       - generates OpenAI embeddings for chunks and
                              queries.
    VectorStoreService     - persists and queries chunks in ChromaDB.
    RetrieverService       - high-level, typed retrieval over the
                              vector store.

This package intentionally contains no FastAPI routes, no LangGraph
nodes, and no AI agents. It exposes only framework-agnostic services
that a future application-layer use case (e.g., "ingest a document" or
"build agent context") will compose together, per Clean Architecture.

Typical composition (illustrative only - not implemented in this
package):

    loader = DocumentLoaderService()
    splitter = TextSplitterService()
    embeddings = EmbeddingService()
    store = VectorStoreService(embedding_service=embeddings)
    retriever = RetrieverService(vector_store=store)

    raw_docs = loader.load(file_path)
    chunks = splitter.split_into_chunks(raw_docs, project_id=..., ...)
    store.add_chunks(chunks)
    results = retriever.retrieve(RetrievalQuery(project_id=..., query_text=...))
"""

from app.rag.document_loader import SUPPORTED_EXTENSIONS, DocumentLoaderService
from app.rag.embedding_service import EmbeddingService
from app.rag.exceptions import (
    DocumentLoadError,
    EmbeddingGenerationError,
    RAGError,
    RetrievalError,
    TextSplittingError,
    UnsupportedFileTypeError,
    VectorStoreError,
)
from app.rag.models import (
    ChunkMetadata,
    DocumentChunk,
    IngestionRequest,
    IngestionResult,
    RetrievalQuery,
    RetrievalResult,
)
from app.rag.retriever import RetrieverService
from app.rag.text_splitter import TextSplitterService
from app.rag.vector_store import VectorStoreService

__all__ = [
    # Services
    "DocumentLoaderService",
    "TextSplitterService",
    "EmbeddingService",
    "VectorStoreService",
    "RetrieverService",
    # Models
    "ChunkMetadata",
    "DocumentChunk",
    "IngestionRequest",
    "IngestionResult",
    "RetrievalQuery",
    "RetrievalResult",
    # Constants
    "SUPPORTED_EXTENSIONS",
    # Exceptions
    "RAGError",
    "UnsupportedFileTypeError",
    "DocumentLoadError",
    "TextSplittingError",
    "EmbeddingGenerationError",
    "VectorStoreError",
    "RetrievalError",
]