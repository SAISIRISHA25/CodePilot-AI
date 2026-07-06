"""
Question-answering use case.

``QueryService`` composes ``app.rag.retriever.RetrieverService`` and
``app.llm.llm_service.LLMService`` (via ``PromptBuilder``) into the
complete retrieval-augmented question-answering pipeline: retrieve
relevant chunks for a project-scoped question, ground a prompt in them,
and invoke the LLM to produce a cited answer.

Design decision:
    Retrieval and generation are two genuinely different concerns
    (finding relevant text vs. producing fluent language grounded in
    it), each already owned by its own package. This service's only
    job is to compose them correctly and translate their failures into
    one consistent exception type - it contains no retrieval logic and
    no prompt-wording logic of its own.
"""

import logging

from app.application.exceptions import QueryServiceError
from app.application.models import QueryResponse, QuerySource
from app.core.constants import DocumentType
from app.llm.exceptions import LLMError
from app.llm.llm_service import LLMService
from app.llm.models import LLMRequest
from app.llm.prompt_builder import PromptBuilder
from app.rag.exceptions import RAGError
from app.rag.models import RetrievalQuery
from app.rag.retriever import RetrieverService

logger = logging.getLogger("codepilot.application.query_service")


class QueryService:
    """Answers project-scoped questions grounded in retrieved document chunks."""

    def __init__(self, retriever: RetrieverService, llm_service: LLMService) -> None:
        """Initialize the query pipeline with its two collaborators.

        Args:
            retriever: Retrieves relevant, project-scoped chunks for a
                question.
            llm_service: Generates a grounded answer from the retrieved
                chunks.
        """
        self._retriever = retriever
        self._llm_service = llm_service

    def answer_question(
        self,
        project_id: str,
        question: str,
        top_k: int = 5,
        document_type: DocumentType | None = None,
    ) -> QueryResponse:
        """Answer a question, grounded in the project's ingested documents.

        Args:
            project_id: Restricts retrieval to this project's documents
                only.
            question: The natural-language question to answer.
            top_k: Maximum number of chunks to retrieve as grounding
                context.
            document_type: Optional filter restricting retrieval to a
                single document category.

        Returns:
            QueryResponse: The generated answer, its sources, and token
            usage.

        Raises:
            QueryServiceError: If retrieval fails, if no relevant
                context can be found for the question, or if the
                underlying LLM invocation fails.
        """
        retrieval_query = RetrievalQuery(
            project_id=project_id,
            query_text=question,
            top_k=top_k,
            document_type=document_type,
        )

        try:
            retrieval_results = self._retriever.retrieve(retrieval_query)
        except RAGError as exc:
            logger.error(
                "query_service.retrieval_failed",
                extra={"project_id": project_id, "error": str(exc)},
            )
            raise QueryServiceError(
                f"Failed to retrieve context for project '{project_id}': {exc}"
            ) from exc

        if not retrieval_results:
            logger.warning(
                "query_service.no_context_found",
                extra={"project_id": project_id, "question": question},
            )
            return QueryResponse(
                question=question,
                answer="No relevant information found.",
                sources=[],
                token_usage=None,
                model=None,
            )

        context_chunks = [result.content for result in retrieval_results]

        try:
            messages = PromptBuilder.build_rag_qa_prompt(
                question=question, context_chunks=context_chunks
            )
            response = self._llm_service.complete(LLMRequest(messages=messages))
        except LLMError as exc:
            logger.error(
                "query_service.llm_invocation_failed",
                extra={"project_id": project_id, "error": str(exc)},
            )
            raise QueryServiceError(
                f"Failed to generate an answer for project '{project_id}': {exc}"
            ) from exc

        sources = [
            QuerySource(
                filename=result.metadata.filename,
                chunk_index=result.metadata.chunk_index,
                relevance_score=result.relevance_score,
            )
            for result in retrieval_results
        ]

        logger.info(
            "query_service.answer_succeeded",
            extra={"project_id": project_id, "source_count": len(sources)},
        )

        return QueryResponse(
            question=question,
            answer=response.content,
            sources=sources,
            token_usage=response.usage,
            model=response.model,
        )