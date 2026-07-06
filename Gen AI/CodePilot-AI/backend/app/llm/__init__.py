"""
LLM package for CodePilot AI.

Provides the application's single, controlled seam for communicating
with OpenAI:

    LLMService     - manages the OpenAI client and executes chat
                     completion requests, with retry/timeout handling
                     and typed responses. The ONLY component permitted
                     to import the `openai` package or call its API.
    PromptBuilder   - constructs reusable, structured chat prompts
                      (system prompts, RAG question-answering prompts,
                      document-grounded generation prompts) as plain
                      `ChatMessage` objects, with no network dependency.

This package intentionally contains no FastAPI routes, no LangGraph
nodes, no AI agents, and no persistence code. It exposes only
framework-agnostic services that a future application-layer use case or
agent (in a later module) will compose together.

Typical composition (illustrative only - not implemented in this
package):

    llm_service = LLMService()
    messages = PromptBuilder.build_rag_qa_prompt(
        question="What authentication method does the API use?",
        context_chunks=[chunk.content for chunk in retrieval_results],
    )
    response = llm_service.complete(LLMRequest(messages=messages))
"""

from app.llm.exceptions import (
    InvalidPromptError,
    LLMConnectionError,
    LLMError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.llm.llm_service import LLMService
from app.llm.models import ChatMessage, LLMRequest, LLMResponse, MessageRole, TokenUsage
from app.llm.prompt_builder import PromptBuilder

__all__ = [
    # Services
    "LLMService",
    "PromptBuilder",
    # Models
    "ChatMessage",
    "MessageRole",
    "TokenUsage",
    "LLMRequest",
    "LLMResponse",
    # Exceptions
    "LLMError",
    "InvalidPromptError",
    "LLMConnectionError",
    "LLMTimeoutError",
    "LLMResponseError",
]