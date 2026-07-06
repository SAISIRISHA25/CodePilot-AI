"""
Exception hierarchy for the LLM package.

Every failure mode specific to LLM invocation is represented by a
dedicated exception class rooted at ``LLMError``. Callers of
``LLMService`` never need to know about the OpenAI SDK's own exception
types (``openai.APIConnectionError``, ``openai.RateLimitError``, etc.) -
``LLMService`` translates every one of them into exactly one of the
types defined here, at the single boundary where this application talks
to OpenAI.

Design decision:
    These exceptions carry no HTTP status codes or FastAPI-specific
    concerns - this package has no knowledge of the interface layer
    (Clean Architecture boundary). Translating an ``LLMError`` into an
    HTTP response is the responsibility of a future API exception
    handler, not this module.
"""


class LLMError(Exception):
    """Base exception for all errors raised by the LLM package.

    Catching this exception type catches any failure originating from
    prompt construction or LLM invocation.
    """


class InvalidPromptError(LLMError):
    """Raised when a prompt or request payload is malformed.

    Covers cases such as an empty message list, an empty question or
    context passed to a prompt builder, or a request whose parameters
    fail validation before any network call is attempted. Raised early
    and deliberately, before any OpenAI API call, to avoid spending a
    request on input that could never succeed.
    """


class LLMConnectionError(LLMError):
    """Raised when the LLM service cannot reach the OpenAI API.

    Covers network-level failures (DNS resolution, connection refused,
    TLS handshake failures) surfaced by the OpenAI SDK as
    ``APIConnectionError``, after all configured retries have been
    exhausted.
    """


class LLMTimeoutError(LLMError):
    """Raised when an OpenAI API call exceeds its configured timeout.

    Raised after all configured retries have been exhausted, so callers
    can distinguish "the request never got a response in time" from a
    general connectivity failure.
    """


class LLMResponseError(LLMError):
    """Raised when the OpenAI API returns an error or malformed response.

    Covers non-2xx API responses (authentication failures, invalid
    requests, rate limiting after retries are exhausted, server errors)
    as well as cases where a syntactically successful response cannot be
    parsed into a valid ``LLMResponse`` (e.g., missing choices or usage
    data).
    """