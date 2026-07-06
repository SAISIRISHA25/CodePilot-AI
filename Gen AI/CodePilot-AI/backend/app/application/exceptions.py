"""Application-layer exception hierarchy for CodePilot AI."""


class ApplicationError(Exception):
    """Base exception for all application-layer failures."""


class IngestionServiceError(ApplicationError):
    """Raised when document ingestion fails."""


class QueryServiceError(ApplicationError):
    """Raised when the query-answering pipeline fails."""


class AgentRoutingError(ApplicationError):
    """Raised when an agent cannot be dispatched correctly."""
