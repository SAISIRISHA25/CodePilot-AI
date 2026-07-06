"""Exception hierarchy for the agents package."""


class AgentError(Exception):
    """Base exception for all agent-related failures."""


class AgentValidationError(AgentError):
    """Raised when an agent receives invalid or incomplete input."""


class AgentExecutionError(AgentError):
    """Raised when an agent fails while executing its work."""


class UnsupportedAgentError(AgentError):
    """Raised when a requested agent type is not registered."""
