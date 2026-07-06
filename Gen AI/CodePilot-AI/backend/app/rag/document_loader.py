"""
Document loading service.

Responsible for one thing only: turning a file on disk into a list of
LangChain ``Document`` objects (raw text plus loader-provided metadata,
such as page numbers for PDFs). This service knows nothing about
chunking, embeddings, project IDs, or ChromaDB - those concerns belong
to later stages of the pipeline (``text_splitter``, ``embedding_service``,
``vector_store``).

Design decision:
    File-type detection is based on file extension and dispatched via a
    simple mapping to the appropriate LangChain loader class
    (``PyPDFLoader``, ``Docx2txtLoader``, ``TextLoader``). This keeps the
    service open for extension (Open/Closed Principle) - adding support
    for a new file type later means adding one entry to
    ``SUPPORTED_EXTENSIONS`` and one branch in ``_get_loader``, without
    touching any other method.
"""

import logging
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document

from app.rag.exceptions import DocumentLoadError, UnsupportedFileTypeError

logger = logging.getLogger("codepilot.rag.document_loader")

# Mapping of supported file extensions (lowercase, including the dot) to
# a short label, used for validation and error messages. The actual
# loader class selection happens in `_get_loader`, kept separate so this
# set can be inspected/tested independently of loader instantiation.
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx", ".txt"})


class DocumentLoaderService:
    """Loads PDF, DOCX, and TXT files into LangChain ``Document`` objects.

    This class is stateless and safe to reuse across many ingestion
    requests - it holds no per-document state between calls.
    """

    def load(self, file_path: str) -> list[Document]:
        """Load a document from disk into a list of LangChain Documents.

        A single source file may yield multiple ``Document`` objects
        (e.g., PyPDFLoader returns one ``Document`` per PDF page). This
        is intentional and handled by the downstream text splitter,
        which flattens and re-chunks across all of them.

        Args:
            file_path: Filesystem path to the document to load.

        Returns:
            list[Document]: The raw LangChain documents produced by the
            appropriate loader for this file's type.

        Raises:
            UnsupportedFileTypeError: If the file's extension is not one
                of ``SUPPORTED_EXTENSIONS``.
            DocumentLoadError: If the file does not exist, or the
                underlying loader fails to parse it.
        """
        path = Path(file_path)

        if not path.exists():
            raise DocumentLoadError(f"File not found: {file_path}")

        if not path.is_file():
            raise DocumentLoadError(f"Path is not a file: {file_path}")

        loader = self._get_loader(path)

        try:
            documents = loader.load()
        except Exception as exc:
            # Any underlying loader failure (corrupted PDF, unreadable
            # DOCX, encoding issue in a TXT file) is wrapped in our own
            # exception type so callers never need to know about
            # LangChain/pypdf/docx2txt-specific exception classes.
            logger.exception(
                "document_loader.load_failed",
                extra={"file_path": file_path},
            )
            raise DocumentLoadError(
                f"Failed to load document '{path.name}': {exc}"
            ) from exc

        if not documents:
            raise DocumentLoadError(f"No content extracted from document: {path.name}")

        logger.info(
            "document_loader.load_succeeded",
            extra={"file_path": file_path, "document_count": len(documents)},
        )
        return documents

    def _get_loader(
        self, path: Path
    ) -> PyPDFLoader | Docx2txtLoader | TextLoader:
        """Select the appropriate LangChain loader for a file's extension.

        Args:
            path: The file path whose extension determines the loader.

        Returns:
            The instantiated LangChain loader for this file type.

        Raises:
            UnsupportedFileTypeError: If the extension is not supported.
        """
        extension = path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file type '{extension}' for file '{path.name}'. "
                f"Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        if extension == ".pdf":
            return PyPDFLoader(str(path))
        if extension == ".docx":
            return Docx2txtLoader(str(path))
        # `.txt` is the only remaining supported extension at this point.
        return TextLoader(str(path), encoding="utf-8")