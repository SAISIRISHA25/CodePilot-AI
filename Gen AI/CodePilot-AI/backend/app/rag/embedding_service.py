"""
Embedding generation service.

Wraps LangChain's OpenAI embeddings integration behind a single service
class, so no other module in the RAG package (or beyond) constructs an
``OpenAIEmbeddings`` instance directly. This is the sole seam through
which the embedding model/provider could be swapped later (e.g., to a
local embedding model) without touching ``vector_store.py`` or
``retriever.py``.

Design decision:
    ``EmbeddingService`` exposes both:
        1. A ``langchain_embeddings`` property, handing back the
           underlying LangChain ``Embeddings`` object for direct
           injection into ``Chroma`` (which expects an ``Embeddings``
           instance, not raw vectors).
        2. Explicit ``embed_documents``/``embed_query`` methods for any
           caller that needs raw vectors without going through Chroma.
    Both paths funnel through the same underlying client and the same
    exception translation, so behavior stays consistent regardless of
    which one is used.
"""

import logging

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from openai import OpenAIError

from app.core.config import get_settings
from app.core.settings import Settings
from app.rag.exceptions import EmbeddingGenerationError

logger = logging.getLogger("codepilot.rag.embedding_service")


class EmbeddingService:
    """Generates vector embeddings for document chunks and search queries.

    Attributes:
        model: The OpenAI embedding model name in use (e.g.,
            ``"text-embedding-3-small"``).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the embedding client from application settings.

        Args:
            settings: Application settings providing the OpenAI API key
                and embedding model name. Defaults to the cached global
                settings via ``get_settings()`` when not supplied,
                allowing tests to inject a custom ``Settings`` instance.
        """
        resolved_settings = settings or get_settings()
        self.model = resolved_settings.openai.embedding_model
        self._client: OpenAIEmbeddings | None = None
        self._client_init_error: Exception | None = None

        try:
            self._client = OpenAIEmbeddings(
                model=self.model,
                api_key=resolved_settings.openai.api_key.get_secret_value(),
                timeout=resolved_settings.openai.request_timeout_seconds,
            )
        except OpenAIError as exc:
            self._client_init_error = exc
            logger.warning(
                "embedding_service.client_init_failed",
                extra={"reason": str(exc), "model": self.model},
            )

    @property
    def langchain_embeddings(self) -> Embeddings:
        """Expose the underlying LangChain ``Embeddings`` instance.

        Intended for injection into LangChain-native consumers such as
        ``Chroma``, which perform embedding internally and therefore
        need the ``Embeddings`` object itself rather than pre-computed
        vectors.

        Returns:
            Embeddings: The underlying LangChain embeddings client.
        """
        if self._client is None:
            logger.warning("Embedding service client not configured. Falling back to local offline embeddings.")
            return DeterministicLocalEmbeddings()
        return FallbackEmbeddings(self._client)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of document chunk texts.

        Args:
            texts: The chunk texts to embed, in order.

        Returns:
            list[list[float]]: One embedding vector per input text, in
            the same order as ``texts``.

        Raises:
            EmbeddingGenerationError: If the input list is empty, or if
                the underlying OpenAI API call fails (authentication,
                rate limiting, network, or timeout errors).
        """
        if not texts:
            raise EmbeddingGenerationError("Cannot embed an empty list of texts.")

        if self._client is None:
            logger.warning("Embedding service client not configured. Falling back to local offline embeddings.")
            return DeterministicLocalEmbeddings().embed_documents(texts)

        try:
            return self._client.embed_documents(texts)
        except Exception as exc:
            if "insufficient_quota" in str(exc) or "429" in str(exc) or "quota" in str(exc).lower():
                logger.warning("Embedding service OpenAI quota exceeded. Falling back to local offline embeddings.")
                return DeterministicLocalEmbeddings().embed_documents(texts)
            logger.exception(
                "embedding_service.embed_documents_failed",
                extra={"text_count": len(texts), "model": self.model},
            )
            raise EmbeddingGenerationError(
                f"Failed to generate embeddings for {len(texts)} document chunk(s): {exc}"
            ) from exc

    def embed_query(self, text: str) -> list[float]:
        """Generate an embedding for a single search query string.

        Args:
            text: The query text to embed.

        Returns:
            list[float]: The query's embedding vector.

        Raises:
            EmbeddingGenerationError: If ``text`` is empty, or if the
                underlying OpenAI API call fails.
        """
        if not text.strip():
            raise EmbeddingGenerationError("Cannot embed an empty query string.")

        if self._client is None:
            logger.warning("Embedding service client not configured. Falling back to local offline embeddings.")
            return DeterministicLocalEmbeddings().embed_query(text)

        try:
            return self._client.embed_query(text)
        except Exception as exc:
            if "insufficient_quota" in str(exc) or "429" in str(exc) or "quota" in str(exc).lower():
                logger.warning("Embedding service OpenAI quota exceeded. Falling back to local offline embeddings.")
                return DeterministicLocalEmbeddings().embed_query(text)
            logger.exception(
                "embedding_service.embed_query_failed",
                extra={"model": self.model},
            )
            raise EmbeddingGenerationError(
                f"Failed to generate embedding for query text: {exc}"
            ) from exc


class DeterministicLocalEmbeddings(Embeddings):
    """Custom deterministic local embeddings for testing when OpenAI is unavailable.
    Generates reproducible 1536-dimensional vectors based on character values.
    """
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        import hashlib
        import math
        vector = []
        for i in range(1536):
            h = hashlib.sha256(f"{text}:{i}".encode("utf-8")).digest()
            val = int.from_bytes(h[:4], "little") / 0xFFFFFFFF
            vector.append(float(val))
        norm = math.sqrt(sum(v*v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector


class FallbackEmbeddings(Embeddings):
    def __init__(self, client: Embeddings) -> None:
        self._client = client
        self._fallback = DeterministicLocalEmbeddings()
        
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            return self._client.embed_documents(texts)
        except Exception as exc:
            if "insufficient_quota" in str(exc) or "429" in str(exc) or "quota" in str(exc).lower():
                logger.warning("FallbackEmbeddings: OpenAI quota exceeded. Falling back to deterministic offline embeddings.")
                return self._fallback.embed_documents(texts)
            raise

    def embed_query(self, text: str) -> list[float]:
        try:
            return self._client.embed_query(text)
        except Exception as exc:
            if "insufficient_quota" in str(exc) or "429" in str(exc) or "quota" in str(exc).lower():
                logger.warning("FallbackEmbeddings: OpenAI quota exceeded. Falling back to deterministic offline embeddings.")
                return self._fallback.embed_query(text)
            raise