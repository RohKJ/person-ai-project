class AgentError(RuntimeError):
    """Base error for agent execution failures."""


class AgentConfigurationError(AgentError):
    """Raised when a requested agent provider is not configured."""


class AgentExecutionError(AgentError):
    """Raised when an agent provider cannot complete a request."""
