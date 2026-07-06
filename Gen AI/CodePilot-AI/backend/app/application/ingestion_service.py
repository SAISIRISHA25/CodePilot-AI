"""
Document ingestion use case.

``IngestionService`` composes the RAG package's individual services -
``DocumentLoaderService``, ``TextSplitterService``, ``EmbeddingService``,
and ``VectorStoreService`` - into the single, complete ingestion
pipeline: load a file, split it into metadata-tagged chunks, and
persist those chunks as embedded vectors.

Design decision:
    This is exactly the composition that ``app.rag``'s own package
    docstring describes as "illustrative only - not implemented in that
    package." That was deliberate: the RAG package exposes composable
    building blocks, and gluing them into a use case is application-layer
    business logic, which belongs here, one layer up, per Clean
    Architecture. Every collaborator is received through constructor
    injection - this service never constructs a ``DocumentLoaderService``
    or ``Chroma`` instance itself.
"""

import logging
from datetime import UTC, datetime

from app.application.exceptions import IngestionServiceError
from app.application.models import IngestionResult
from app.core.constants import DocumentType
from app.rag.document_loader import DocumentLoaderService
from app.rag.embedding_service import EmbeddingService
from app.rag.exceptions import RAGError
from app.rag.text_splitter import TextSplitterService
from app.rag.vector_store import VectorStoreService

logger = logging.getLogger("codepilot.application.ingestion_service")


class IngestionService:
    """Orchestrates loading, splitting, embedding, and storing a document."""

    def __init__(
        self,
        document_loader: DocumentLoaderService,
        text_splitter: TextSplitterService,
        embedding_service: EmbeddingService,
        vector_store: VectorStoreService,
    ) -> None:
        """Initialize the ingestion pipeline with its four collaborators.

        Args:
            document_loader: Loads PDF/DOCX/TXT files into raw LangChain
                documents.
            text_splitter: Splits raw documents into metadata-tagged
                chunks.
            embedding_service: The embedding client used (via
                ``vector_store``) to embed chunks. Held directly by this
                service so the embedding model in use can be recorded on
                every ``IngestionResult`` for auditability, even though
                the actual embedding computation happens inside
                ``vector_store.add_chunks``.
            vector_store: Persists embedded chunks into ChromaDB. Must
                have been constructed with the same ``embedding_service``
                instance passed here, so the model recorded on the
                result actually matches what was used to embed.
        """
        self._document_loader = document_loader
        self._text_splitter = text_splitter
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    def ingest_document(
        self,
        project_id: str,
        file_path: str,
        filename: str,
        document_type: DocumentType,
        uploaded_at: datetime | None = None,
    ) -> IngestionResult:
        """Ingest a single document: load, split, embed, and store it.

        Args:
            project_id: The project this document belongs to.
            file_path: Filesystem path to the document to ingest.
            filename: Original filename, preserved for metadata/display.
            document_type: Category of the document being ingested.
            uploaded_at: UTC timestamp of upload. Defaults to the
                current time when not supplied.

        Returns:
            IngestionResult: The typed outcome of this ingestion,
            including the number of chunks stored and their IDs.

        Raises:
            IngestionServiceError: If loading, splitting, or storing the
                document fails for any reason.
        """
        resolved_uploaded_at = uploaded_at or datetime.now(UTC)

        logger.info(
            "ingestion_service.ingest_started",
            extra={"project_id": project_id, "doc_filename": filename},
        )

        try:
            raw_documents = self._document_loader.load(file_path)

            chunks = self._text_splitter.split_into_chunks(
                documents=raw_documents,
                project_id=project_id,
                filename=filename,
                document_type=document_type,
                uploaded_at=resolved_uploaded_at,
            )

            chunk_ids = self._vector_store.add_chunks(chunks)

        except RAGError as exc:
            logger.error(
                "ingestion_service.ingest_failed",
                extra={"project_id": project_id, "doc_filename": filename, "error": str(exc)},
            )
            raise IngestionServiceError(
                f"Failed to ingest document '{filename}' for project '{project_id}': {exc}"
            ) from exc

        # All chunks produced by a single `split_into_chunks` call share
        # one source_document_id - safe to read it from the first chunk.
        source_document_id = chunks[0].metadata.source_document_id

        result = IngestionResult(
            project_id=project_id,
            filename=filename,
            document_type=document_type,
            source_document_id=source_document_id,
            total_chunks=len(chunks),
            chunk_ids=chunk_ids,
            embedding_model=self._embedding_service.model,
            ingested_at=resolved_uploaded_at.isoformat(),
        )

        logger.info(
            "ingestion_service.ingest_succeeded",
            extra={
                "project_id": project_id,
                "doc_filename": filename,
                "total_chunks": result.total_chunks,
            },
        )
        return result