"""Custom exceptions for Agent Feng.

This module contains application-specific exceptions organized in a hierarchy.
All custom exceptions inherit from AgentFengError, making it easy to catch
all application-specific errors in a single except clause.

Exception Hierarchy:
    AgentFengError (base)
    ├── ConfigurationError
    │   ├── EnvironmentError
    │   └── ConfigFileError
    ├── ContextError
    └── InfrastructureError
        ├── MCPError
        └── AIProviderError

Example:
    Catch all application errors::

        from agent_feng.core.exceptions import AgentFengError

        try:
            run_application()
        except AgentFengError as e:
            logger.error("Application error: %s", e)

    Catch specific errors::

        from agent_feng.core.exceptions import ConfigurationError

        try:
            load_config()
        except ConfigurationError as e:
            logger.error("Configuration failed: %s", e)
"""

from __future__ import annotations


class AgentFengError(Exception):
    """Base exception for all Agent Feng errors.

    All custom exceptions in this application inherit from this class,
    allowing callers to catch all application-specific errors.

    :param message: Human-readable error description.

    Example:
        Raise a base error::

            raise AgentFengError("Something went wrong")
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(AgentFengError):
    """Error related to application configuration.

    Raised when configuration loading, parsing, or validation fails.

    Example:
        Raise a configuration error::

            raise ConfigurationError("Invalid configuration format")
    """


class EnvironmentConfigError(ConfigurationError):
    """Error related to environment variable configuration.

    Raised when required environment variables are missing or invalid.

    :param variable: Name of the problematic environment variable.
    :param message: Human-readable error description.

    Example:
        Raise for missing variable::

            raise EnvironmentConfigError("API_KEY", "Required variable not set")
    """

    def __init__(self, variable: str, message: str) -> None:
        self.variable = variable
        super().__init__(f"Environment variable '{variable}': {message}")


class ConfigFileError(ConfigurationError):
    """Error related to configuration file loading.

    Raised when a configuration file cannot be read, parsed, or validated.

    :param file_path: Path to the problematic configuration file.
    :param message: Human-readable error description.

    Example:
        Raise for invalid YAML::

            raise ConfigFileError("/path/to/config.yaml", "Invalid YAML syntax")
    """

    def __init__(self, file_path: str, message: str) -> None:
        self.file_path = file_path
        super().__init__(f"Configuration file '{file_path}': {message}")


# =============================================================================
# Context Errors
# =============================================================================


class ContextError(AgentFengError):
    """Error related to application context.

    Raised when context creation, validation, or access fails.

    Example:
        Raise a context error::

            raise ContextError("Context not initialized")
    """


# =============================================================================
# Infrastructure Errors
# =============================================================================


class InfrastructureError(AgentFengError):
    """Base error for infrastructure layer failures.

    Raised when external system integrations fail.

    Example:
        Raise an infrastructure error::

            raise InfrastructureError("External service unavailable")
    """


class MCPError(InfrastructureError):
    """Error related to MCP (Model Context Protocol) operations.

    Raised when MCP server communication fails.

    :param server_name: Name of the MCP server (if known).
    :param message: Human-readable error description.

    Example:
        Raise for connection failure::

            raise MCPError("tools-server", "Connection refused")
    """

    def __init__(self, server_name: str | None, message: str) -> None:
        self.server_name = server_name
        prefix = f"MCP server '{server_name}'" if server_name else "MCP"
        super().__init__(f"{prefix}: {message}")


class AIProviderError(InfrastructureError):
    """Error related to AI provider operations.

    Raised when AI provider API calls fail.

    :param provider: Name of the AI provider (e.g., "openai", "anthropic").
    :param message: Human-readable error description.

    Example:
        Raise for API error::

            raise AIProviderError("openai", "Rate limit exceeded")
    """

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"AI provider '{provider}': {message}")
