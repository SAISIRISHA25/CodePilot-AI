"""
Exception hierarchy for the RAG (Retrieval Augmented Generation) package.

Every failure mode specific to document ingestion and retrieval is
represented by a dedicated exception class rooted at ``RAGError``. This
lets calling code (future use cases, API exception handlers) catch
either a specific failure type or the whole ``RAGError`` family, rather
than catching broad, ambiguous exceptions like ``Exception`` or
library-specific errors leaking out of LangChain/ChromaDB/OpenAI.

Design decision:
    These exceptions intentionally carry no HTTP status codes or
    FastAPI-specific concerns - this package has no knowledge of the
    interface layer (Clean Architecture boundary). Translating a
    ``RAGError`` into an HTTP response is the responsibility of a future
    API route/exception handler, not this module.
"""


class RAGError(Exception):
    """Base exception for all errors raised by the RAG package.

    Catching this exception type catches any failure originating from
    document loading, splitting, embedding, vector storage, or
    retrieval.
    """


class UnsupportedFileTypeError(RAGError):
    """Raised when a document's file type is not supported for ingestion.

    Currently supported types are PDF, DOCX, and TXT, as defined by
    ``document_loader.SUPPORTED_EXTENSIONS``.
    """


class DocumentLoadError(RAGError):
    """Raised when a document fails to load or parse from disk.

    Covers cases such as a missing file, a corrupted PDF, or a DOCX file
    that cannot be opened by the underlying LangChain loader.
    """


class TextSplittingError(RAGError):
    """Raised when splitting loaded documents into chunks fails.

    Typically indicates malformed or empty document content that the
    text splitter cannot process meaningfully.
    """


class EmbeddingGenerationError(RAGError):
    """Raised when generating vector embeddings fails.

    Covers OpenAI API failures (auth errors, rate limits, timeouts) that
    occur while embedding document chunks or query text.
    """


class VectorStoreError(RAGError):
    """Raised when a ChromaDB operation fails.

    Covers failures while adding chunks to, or querying, the underlying
    ChromaDB collection.
    """


class RetrievalError(RAGError):
    """Raised when retrieving relevant chunks for a query fails.

    Distinguished from ``VectorStoreError`` so callers can tell apart a
    low-level storage failure from a higher-level retrieval/query
    composition failure (e.g., invalid filter construction).
    """