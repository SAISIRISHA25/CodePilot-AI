"""
Pydantic data models for the RAG (Retrieval Augmented Generation) package.

These models define the structured contracts passed between the RAG
package's services (loader -> splitter -> embedding -> vector store ->
retriever). No plain dicts or bare LangChain objects cross a service
boundary in this package's public API - everything is a typed,
validated Pydantic model.

Design decision:
    ``ChunkMetadata`` is deliberately explicit about every field the
    architecture requires to be stored per chunk (project_id, filename,
    document_type, uploaded_at, chunk_index). Keeping this as its own
    model - rather than a loose ``dict[str, Any]`` - means ChromaDB
    metadata writes are always well-formed and IDE/type-checker
    verifiable.
"""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.constants import DocumentType


class ChunkMetadata(BaseModel):
    """Metadata attached to every stored document chunk.

    This exact set of fields is mandated by the project's architecture:
    every chunk written to ChromaDB must carry ``project_id``,
    ``filename``, ``document_type``, ``uploaded_at``, and
    ``chunk_index``.

    Attributes:
        project_id: The owning project's identifier. Used to scope
            retrieval so one project's documents never leak into
            another's search results (multi-tenancy isolation).
        filename: Original filename of the source document.
        document_type: The category of the source document (BRD, FRS,
            architecture doc, API spec, or coding standards).
        uploaded_at: UTC timestamp of when the source document was
            uploaded/ingested.
        chunk_index: Zero-based position of this chunk within its
            source document, preserving reading order.
        source_document_id: Stable identifier grouping all chunks that
            originated from the same source document, independent of
            filename (which is not guaranteed unique across uploads).
    """

    project_id: str = Field(description="Owning project identifier.")
    filename: str = Field(description="Original filename of the source document.")
    document_type: DocumentType = Field(description="Category of the source document.")
    uploaded_at: datetime = Field(description="UTC timestamp of document upload.")
    chunk_index: int = Field(ge=0, description="Zero-based chunk position within the document.")
    source_document_id: str = Field(
        description="Identifier grouping all chunks from the same source document."
    )

    def to_chroma_metadata(self) -> dict[str, str | int]:
        """Flatten this model into a ChromaDB-compatible metadata dict.

        ChromaDB metadata values must be primitive types (str, int,
        float, bool) - it cannot store nested objects or ``datetime``
        instances directly. This method performs that flattening in
        exactly one place so every write path stays consistent.

        Returns:
            dict[str, str | int]: A flat metadata dictionary safe to
            pass to ChromaDB's ``add_texts``/``add_documents`` calls.
        """
        return {
            "project_id": self.project_id,
            "filename": self.filename,
            "document_type": self.document_type.value,
            "uploaded_at": self.uploaded_at.isoformat(),
            "chunk_index": self.chunk_index,
            "source_document_id": self.source_document_id,
        }


class DocumentChunk(BaseModel):
    """A single chunk of text extracted from a source document.

    Attributes:
        id: Unique identifier for this chunk, used as its ChromaDB
            document ID (enables idempotent upserts/deletes later).
        content: The chunk's raw text content.
        metadata: Structured metadata describing this chunk's
            provenance (see ``ChunkMetadata``).
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique chunk identifier.")
    content: str = Field(min_length=1, description="Raw text content of this chunk.")
    metadata: ChunkMetadata = Field(description="Structured provenance metadata.")


class IngestionRequest(BaseModel):
    """Input parameters for ingesting a single document.

    Attributes:
        project_id: The project this document belongs to.
        file_path: Filesystem path to the document to be ingested.
        filename: Original filename, preserved for metadata/display.
        document_type: Category of the document being ingested.
        uploaded_at: UTC timestamp of upload. Defaults to "now" if not
            explicitly supplied by the caller.
    """

    project_id: str = Field(description="Owning project identifier.")
    file_path: str = Field(description="Filesystem path to the document.")
    filename: str = Field(description="Original filename of the document.")
    document_type: DocumentType = Field(description="Category of the document.")
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of document upload.",
    )


class IngestionResult(BaseModel):
    """Outcome of successfully ingesting a single document.

    Attributes:
        source_document_id: Identifier grouping all chunks produced from
            this ingestion.
        project_id: The project the document was ingested into.
        filename: Original filename of the ingested document.
        total_chunks: Number of chunks produced and stored.
        chunk_ids: The ChromaDB IDs assigned to each stored chunk.
    """

    source_document_id: str = Field(description="Identifier grouping this document's chunks.")
    project_id: str = Field(description="Owning project identifier.")
    filename: str = Field(description="Original filename of the ingested document.")
    total_chunks: int = Field(ge=0, description="Number of chunks produced and stored.")
    chunk_ids: list[str] = Field(default_factory=list, description="Stored chunk IDs.")


class RetrievalQuery(BaseModel):
    """Input parameters for a similarity search against the vector store.

    Attributes:
        project_id: Restrict retrieval to this project's chunks only.
            Always required, enforcing tenant isolation at the query
            level rather than relying on callers to remember a filter.
        query_text: The natural-language query to search with.
        top_k: Maximum number of chunks to return.
        document_type: Optional filter restricting results to a single
            document category (e.g., only API specifications).
    """

    project_id: str = Field(description="Restrict results to this project only.")
    query_text: str = Field(min_length=1, description="Natural-language search query.")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of results.")
    document_type: DocumentType | None = Field(
        default=None, description="Optional document-type filter."
    )


class RetrievalResult(BaseModel):
    """A single retrieved chunk, paired with its relevance score.

    Attributes:
        content: The retrieved chunk's text content.
        metadata: The chunk's stored provenance metadata.
        relevance_score: Similarity score returned by ChromaDB. Lower
            values indicate a closer match, consistent with ChromaDB's
            default distance-based scoring (not a normalized similarity
            percentage).
    """

    content: str = Field(description="Retrieved chunk text content.")
    metadata: ChunkMetadata = Field(description="Chunk provenance metadata.")
    relevance_score: float = Field(description="Distance-based relevance score (lower = closer).")