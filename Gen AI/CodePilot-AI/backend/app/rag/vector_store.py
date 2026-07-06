"""
Vector storage service.

Wraps ChromaDB (via LangChain's ``Chroma`` integration) behind a single
service class. This is the only module in the RAG package that knows
ChromaDB exists - ``retriever.py`` depends on this service's interface,
not on Chroma directly, so the underlying vector database could be
swapped later without touching retrieval logic.

Per the locked architecture, ChromaDB stores vectors and their
associated chunk metadata ONLY. No project metadata-of-record, audit
logs, or session data are ever written here - those belong to SQLite.
"""

import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import get_settings
from app.core.constants import DocumentType
from app.core.settings import Settings
from app.rag.embedding_service import EmbeddingService
from app.rag.exceptions import VectorStoreError
from app.rag.models import DocumentChunk

logger = logging.getLogger("codepilot.rag.vector_store")


class VectorStoreService:
    """Persists and queries document chunks in a ChromaDB collection.

    Attributes:
        collection_name: The ChromaDB collection this service reads
            from and writes to.
        persist_directory: Filesystem path where ChromaDB persists its
            on-disk index.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the vector store client.

        Args:
            embedding_service: Provides the ``Embeddings`` instance
                Chroma uses internally to embed texts on write and
                queries on read. Injected rather than constructed here,
                so both this service and any caller share one
                configured embedding client (Dependency Inversion).
            settings: Application settings providing ChromaDB
                configuration. Defaults to the cached global settings
                when not supplied.
        """
        resolved_settings = settings or get_settings()
        self.collection_name = resolved_settings.chroma.collection_name
        self.persist_directory = resolved_settings.chroma.persist_directory

        self._store = None

        try:
            embedding_function = embedding_service.langchain_embeddings
            self._store = Chroma(
                collection_name=self.collection_name,
                embedding_function=embedding_function,
                persist_directory=self.persist_directory,
            )
        except Exception as exc:
            logger.warning(
                "vector_store.initialization_failed",
                extra={"collection_name": self.collection_name, "reason": str(exc)},
            )
            self._store = None

    def add_chunks(self, chunks: list[DocumentChunk]) -> list[str]:
        """Store a batch of document chunks in the vector store.

        Args:
            chunks: The chunks to persist, each carrying its own
                ``ChunkMetadata`` (project_id, filename, document_type,
                uploaded_at, chunk_index).

        Returns:
            list[str]: The ChromaDB document IDs assigned to the stored
            chunks (equal to each chunk's own ``id`` field).

        Raises:
            VectorStoreError: If ``chunks`` is empty, or if the
                underlying ChromaDB write fails.
        """
        if not chunks:
            raise VectorStoreError("Cannot add an empty list of chunks to the vector store.")

        if self._store is None:
            raise VectorStoreError(
                "Vector store is not available because ChromaDB could not be initialized"
            )

        ids = [chunk.id for chunk in chunks]
        texts = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata.to_chroma_metadata() for chunk in chunks]

        try:
            stored_ids = self._store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        except Exception as exc:
            logger.exception(
                "vector_store.add_chunks_failed",
                extra={"collection_name": self.collection_name, "chunk_count": len(chunks)},
            )
            raise VectorStoreError(
                f"Failed to add {len(chunks)} chunk(s) to ChromaDB: {exc}"
            ) from exc

        logger.info(
            "vector_store.add_chunks_succeeded",
            extra={"collection_name": self.collection_name, "chunk_count": len(chunks)},
        )
        return list(stored_ids)

    def similarity_search(
        self,
        query_text: str,
        project_id: str,
        top_k: int = 5,
        document_type: DocumentType | None = None,
    ) -> list[tuple[Document, float]]:
        """Search for chunks most relevant to a query, scoped to a project.

        Args:
            query_text: The natural-language query to search with.
            project_id: Restricts results to chunks belonging to this
                project only - always enforced, never optional, to
                preserve tenant isolation.
            top_k: Maximum number of results to return.
            document_type: Optional additional filter restricting
                results to a single document category.

        Returns:
            list[tuple[Document, float]]: Matching LangChain documents
            (with their stored metadata) paired with a distance-based
            relevance score, ordered from most to least relevant.

        Raises:
            VectorStoreError: If the underlying ChromaDB query fails.
        """
        if self._store is None:
            raise VectorStoreError(
                "Vector store is not available because ChromaDB could not be initialized"
            )

        metadata_filter: dict[str, str] = {"project_id": project_id}
        if document_type is not None:
            metadata_filter["document_type"] = document_type.value

        try:
            results = self._store.similarity_search_with_score(
                query=query_text,
                k=top_k,
                filter=metadata_filter,
            )
        except Exception as exc:
            logger.exception(
                "vector_store.similarity_search_failed",
                extra={"collection_name": self.collection_name, "project_id": project_id},
            )
            raise VectorStoreError(
                f"Failed to execute similarity search for project '{project_id}': {exc}"
            ) from exc

        logger.info(
            "vector_store.similarity_search_succeeded",
            extra={
                "collection_name": self.collection_name,
                "project_id": project_id,
                "result_count": len(results),
            },
        )
        return results

    def delete_document_chunks(self, source_document_id: str) -> None:
        """Delete all chunks belonging to a document from ChromaDB.

        Args:
            source_document_id: The document identifier grouping the chunks.
        """
        if self._store is None:
            raise VectorStoreError(
                "Vector store is not available because ChromaDB could not be initialized"
            )
        try:
            self._store.delete(where={"source_document_id": source_document_id})
        except Exception as exc:
            logger.exception(
                "vector_store.delete_chunks_failed",
                extra={"collection_name": self.collection_name, "source_document_id": source_document_id},
            )
            raise VectorStoreError(
                f"Failed to delete chunks for document '{source_document_id}': {exc}"
            ) from exc

    def delete_project_chunks(self, project_id: str) -> None:
        """Delete all chunks belonging to a project from ChromaDB.

        Args:
            project_id: The project identifier.
        """
        if self._store is None:
            raise VectorStoreError(
                "Vector store is not available because ChromaDB could not be initialized"
            )
        try:
            self._store.delete(where={"project_id": project_id})
        except Exception as exc:
            logger.exception(
                "vector_store.delete_project_chunks_failed",
                extra={"collection_name": self.collection_name, "project_id": project_id},
            )
            raise VectorStoreError(
                f"Failed to delete chunks for project '{project_id}': {exc}"
            ) from exc