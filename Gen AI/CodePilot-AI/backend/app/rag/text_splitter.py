"""
Text splitting service.

Responsible for two related tasks:
    1. Splitting raw LangChain ``Document`` objects into fixed-size,
       overlapping text chunks using ``RecursiveCharacterTextSplitter``.
    2. Attaching the architecture-mandated metadata (project_id,
       filename, document_type, uploaded_at, chunk_index) to every
       resulting chunk, producing typed ``DocumentChunk`` models.

Design decision:
    Metadata assembly lives here, rather than in ``document_loader`` or
    ``vector_store``, because chunk boundaries - and therefore
    ``chunk_index`` - are only known once splitting has happened. This
    keeps ``document_loader`` ignorant of project/ingestion context (it
    only knows how to read files) and keeps ``vector_store`` ignorant of
    how chunks were produced (it only knows how to persist them).
"""

import logging
from datetime import datetime
from uuid import uuid4

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DocumentType
from app.rag.exceptions import TextSplittingError
from app.rag.models import ChunkMetadata, DocumentChunk

logger = logging.getLogger("codepilot.rag.text_splitter")


class TextSplitterService:
    """Splits documents into chunks and attaches provenance metadata.

    Attributes:
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of overlapping characters between
            consecutive chunks, preserving context across chunk
            boundaries.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """Initialize the splitter with configurable chunk sizing.

        Args:
            chunk_size: Maximum number of characters per chunk. Defaults
                to the project-wide default defined in
                ``app.core.constants``.
            chunk_overlap: Number of overlapping characters between
                consecutive chunks. Defaults to the project-wide default
                defined in ``app.core.constants``.
        """
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # Recursive splitting tries these separators in order,
            # falling back to finer-grained boundaries only when a
            # coarser one doesn't fit within chunk_size - this keeps
            # chunks aligned to paragraph/sentence boundaries whenever
            # possible, which improves downstream retrieval quality.
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_into_chunks(
        self,
        documents: list[Document],
        project_id: str,
        filename: str,
        document_type: DocumentType,
        uploaded_at: datetime,
        source_document_id: str | None = None,
    ) -> list[DocumentChunk]:
        """Split loaded documents into metadata-tagged chunks.

        Args:
            documents: Raw LangChain documents, typically the output of
                ``DocumentLoaderService.load``. May contain multiple
                documents (e.g., one per PDF page); all are flattened
                into a single, sequentially-indexed chunk sequence.
            project_id: The owning project's identifier, stamped onto
                every resulting chunk's metadata.
            filename: Original filename of the source document, stamped
                onto every resulting chunk's metadata.
            document_type: Category of the source document.
            uploaded_at: UTC timestamp of when the source document was
                uploaded.
            source_document_id: Identifier grouping all chunks from this
                ingestion. If not supplied, a new UUID4 is generated,
                shared across every chunk produced by this call.

        Returns:
            list[DocumentChunk]: Chunks in original reading order, each
            carrying a fully populated ``ChunkMetadata``.

        Raises:
            TextSplittingError: If splitting fails, or if no chunks are
                produced from non-empty input documents.
        """
        if not documents:
            raise TextSplittingError("Cannot split an empty document list.")

        resolved_source_document_id = source_document_id or str(uuid4())

        try:
            split_documents = self._splitter.split_documents(documents)
        except Exception as exc:
            logger.exception(
                "text_splitter.split_failed",
                extra={"doc_filename": filename, "project_id": project_id},
            )
            raise TextSplittingError(
                f"Failed to split document '{filename}' into chunks: {exc}"
            ) from exc

        if not split_documents:
            raise TextSplittingError(
                f"Splitting produced zero chunks for document '{filename}'."
            )

        chunks: list[DocumentChunk] = []
        for index, split_document in enumerate(split_documents):
            chunk_metadata = ChunkMetadata(
                project_id=project_id,
                filename=filename,
                document_type=document_type,
                uploaded_at=uploaded_at,
                chunk_index=index,
                source_document_id=resolved_source_document_id,
            )
            chunks.append(
                DocumentChunk(content=split_document.page_content, metadata=chunk_metadata)
            )

        logger.info(
            "text_splitter.split_succeeded",
            extra={
                "doc_filename": filename,
                "project_id": project_id,
                "chunk_count": len(chunks),
            },
        )
        return chunks