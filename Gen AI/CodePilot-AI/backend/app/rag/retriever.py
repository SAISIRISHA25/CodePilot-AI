"""
Retrieval service.

The highest-level service in the RAG package: given a structured
``RetrievalQuery``, it queries the vector store and returns fully typed
``RetrievalResult`` objects. This is the intended entry point for any
future consumer of RAG (e.g., an agent's context-building step) -
callers depend on this service, not on ``VectorStoreService`` or
``EmbeddingService`` directly.

Design decision:
    This service performs the translation between ChromaDB's raw
    ``(Document, score)`` tuples and the package's own typed models. By
    isolating that translation here, ``vector_store.py`` stays a thin,
    ChromaDB-specific wrapper, while every downstream consumer only ever
    sees clean, validated ``RetrievalResult`` objects with a
    reconstructed ``ChunkMetadata``.
"""

import logging
from datetime import datetime

from app.core.constants import DocumentType
from app.rag.exceptions import RetrievalError
from app.rag.models import ChunkMetadata, RetrievalQuery, RetrievalResult
from app.rag.vector_store import VectorStoreService

logger = logging.getLogger("codepilot.rag.retriever")


class RetrieverService:
    """Retrieves relevant document chunks for a given query.

    Attributes:
        vector_store: The underlying vector store service used to
            execute similarity searches.
    """

    def __init__(self, vector_store: VectorStoreService) -> None:
        """Initialize the retriever with its vector store dependency.

        Args:
            vector_store: The vector store service this retriever
                delegates similarity search to. Injected rather than
                constructed here so tests can supply a stub/mock
                implementation without touching ChromaDB.
        """
        self._vector_store = vector_store

    def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        """Retrieve the most relevant chunks for a structured query.

        Args:
            query: The structured retrieval request, including the
                project scope, query text, result limit, and optional
                document-type filter.

        Returns:
            list[RetrievalResult]: Matching chunks with their content,
            reconstructed metadata, and relevance score, ordered from
            most to least relevant.

        Raises:
            RetrievalError: If the underlying vector store query fails,
                or if a stored chunk's metadata cannot be reconstructed
                into a valid ``ChunkMetadata`` (indicates data
                corruption or a schema mismatch in the vector store).
        """
        try:
            raw_results = self._vector_store.similarity_search(
                query_text=query.query_text,
                project_id=query.project_id,
                top_k=query.top_k,
                document_type=query.document_type,
            )
        except Exception as exc:
            # VectorStoreError is already a RAGError subtype, but we
            # re-wrap as RetrievalError so callers of this service only
            # ever need to catch one exception type at this boundary.
            logger.exception(
                "retriever.retrieve_failed",
                extra={"project_id": query.project_id, "query_text": query.query_text},
            )
            raise RetrievalError(
                f"Failed to retrieve chunks for project '{query.project_id}': {exc}"
            ) from exc

        results: list[RetrievalResult] = []
        for document, score in raw_results:
            try:
                metadata = self._reconstruct_metadata(document.metadata)
            except Exception as exc:
                logger.exception(
                    "retriever.metadata_reconstruction_failed",
                    extra={"project_id": query.project_id},
                )
                raise RetrievalError(
                    f"Failed to reconstruct chunk metadata during retrieval: {exc}"
                ) from exc

            results.append(
                RetrievalResult(
                    content=document.page_content,
                    metadata=metadata,
                    relevance_score=score,
                )
            )

        logger.info(
            "retriever.retrieve_succeeded",
            extra={
                "project_id": query.project_id,
                "query_text": query.query_text,
                "result_count": len(results),
            },
        )
        return results

    @staticmethod
    def _reconstruct_metadata(raw_metadata: dict) -> ChunkMetadata:
        """Rebuild a validated ``ChunkMetadata`` from ChromaDB's flat dict.

        ChromaDB stores metadata as a flat dict of primitives (see
        ``ChunkMetadata.to_chroma_metadata``). This performs the inverse
        transformation, re-parsing the ISO timestamp string and document
        type string back into their proper Python types.

        Args:
            raw_metadata: The flat metadata dict as returned by ChromaDB.

        Returns:
            ChunkMetadata: A fully validated metadata model.
        """
        return ChunkMetadata(
            project_id=raw_metadata["project_id"],
            filename=raw_metadata["filename"],
            document_type=DocumentType(raw_metadata["document_type"]),
            uploaded_at=datetime.fromisoformat(raw_metadata["uploaded_at"]),
            chunk_index=int(raw_metadata["chunk_index"]),
            source_document_id=raw_metadata["source_document_id"],
        )