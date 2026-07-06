"""
Pydantic data models for the LLM package.

These models define the structured contract between prompt construction
(``prompt_builder.py``), LLM invocation (``llm_service.py``), and any
future caller (agents, in a later module). No plain dicts or raw OpenAI
SDK objects cross this package's public API - every request into
``LLMService`` and every response out of it is a typed, validated
Pydantic model.

Design decision:
    ``LLMRequest`` deliberately makes ``model``, ``temperature``,
    ``max_tokens``, and ``timeout_seconds`` optional. When omitted,
    ``LLMService`` falls back to its own configured defaults (sourced
    from application settings and package-level constants). This lets
    most callers build a request with just messages, while still
    allowing any individual call to override any parameter explicitly.
"""

from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Valid roles for a single chat message, matching OpenAI's chat API.

    Inherits from ``str`` so values serialize directly into the OpenAI
    SDK's expected ``role`` field without extra conversion.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """A single message in a chat completion conversation.

    Attributes:
        role: Who the message is attributed to (system, user, or
            assistant).
        content: The message's text content.
    """

    role: MessageRole = Field(description="The role attributed to this message.")
    content: str = Field(min_length=1, description="The message's text content.")

    def to_openai_format(self) -> dict[str, str]:
        """Convert this message into the dict shape the OpenAI SDK expects.

        Returns:
            dict[str, str]: A dict with ``role`` and ``content`` keys,
            suitable for inclusion in the ``messages`` list passed to
            the OpenAI chat completions API.
        """
        return {"role": self.role.value, "content": self.content}


class TokenUsage(BaseModel):
    """Token accounting for a single chat completion call.

    Attributes:
        prompt_tokens: Number of tokens consumed by the input messages.
        completion_tokens: Number of tokens generated in the response.
        total_tokens: Sum of prompt and completion tokens, as reported
            by the OpenAI API (stored rather than recomputed, so this
            always matches what was actually billed).
    """

    prompt_tokens: int = Field(ge=0, description="Tokens consumed by the input messages.")
    completion_tokens: int = Field(ge=0, description="Tokens generated in the response.")
    total_tokens: int = Field(ge=0, description="Total tokens billed for this call.")


class LLMRequest(BaseModel):
    """A structured request to generate a chat completion.

    Attributes:
        messages: The full conversation to send, in order. Must contain
            at least one message.
        model: The OpenAI chat model to use. When omitted, ``LLMService``
            falls back to the application's configured default chat
            model.
        temperature: Sampling temperature. When omitted, ``LLMService``
            falls back to the project-wide default defined in
            ``app.core.constants.DEFAULT_LLM_TEMPERATURE``.
        max_tokens: Maximum number of tokens to generate. When omitted,
            ``LLMService`` falls back to its own configured default.
        timeout_seconds: Per-call timeout override. When omitted,
            ``LLMService`` falls back to the application's configured
            default OpenAI request timeout.
    """

    messages: list[ChatMessage] = Field(min_length=1, description="Full conversation to send.")
    model: str | None = Field(default=None, description="OpenAI chat model override.")
    temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Sampling temperature override."
    )
    max_tokens: int | None = Field(
        default=None, ge=1, description="Maximum tokens to generate, if overridden."
    )
    timeout_seconds: float | None = Field(
        default=None, gt=0.0, description="Per-call timeout override, in seconds."
    )


class LLMResponse(BaseModel):
    """A structured chat completion response.

    Attributes:
        content: The generated response text.
        model: The actual model that served this response, as reported
            by the API (may differ from the requested model alias, e.g.
            when OpenAI resolves a version-pinned alias).
        finish_reason: Why generation stopped (e.g., ``"stop"``,
            ``"length"``, ``"content_filter"``).
        usage: Token accounting for this call.
        response_id: The OpenAI API's unique identifier for this
            completion, useful for support/debugging correlation.
    """

    content: str = Field(description="The generated response text.")
    model: str = Field(description="The model that actually served this response.")
    finish_reason: str = Field(description="Why generation stopped.")
    usage: TokenUsage = Field(description="Token accounting for this call.")
    response_id: str = Field(description="OpenAI's unique identifier for this completion.")