"""Abstract base classes, protocols, and enums for Agent Feng.

This module contains foundational types used throughout the application:
- Enums for constrained value sets
- Protocols for interface definitions
- Abstract base classes for inheritance hierarchies

All types defined here should have no dependencies on other application modules
to avoid circular imports.

Example:
    Import enums and protocols::

        from agent_feng.core.abc import Environment, LogLevel
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol


class Environment(StrEnum):
    """Valid application environments.

    Example:
        Check current environment::

            from agent_feng.core.abc import Environment

            if context.environment == Environment.PRODUCTION:
                enable_strict_mode()
    """

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Valid logging levels.

    Example:
        Configure logging level::

            from agent_feng.core.abc import LogLevel

            level = LogLevel.DEBUG
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecretsProvider(Protocol):
    """Protocol for secrets provider implementations.

    Example:
        Implement a custom secret provider::

            from agent_feng.core.abc import SecretProvider

            class MySecretProvider:
                ...
    """

    def get_secret(self, secret_name: str, default_value: str | None = None) -> str:
        """Retrieve a secret value by key.

        :param key: The key identifying the secret.
        :returns: The secret value.
        """
        ...


class AIModelAdapter[M](Protocol):
    """Protocol for AI model adapter implementations.

    Example:
        Implement a custom AI model adapter::

            from agent_feng.core.abc import AIModelAdapter

            class MyAIModelAdapter:
                ...
    """

    @property
    def model(self) -> M:
        """Get the underlying AI model identifier.

        :returns: The AI model identifier.
        """
        ...


class AgentProvider[A, T, R](Protocol):
    """Protocol for agent provider implementations.

    Example:
        Implement a custom agent provider::

            from agent_feng.core.abc import AgentProvider

            class MyAgentProvider:
                ...
    """

    @property
    def agent(self) -> A:
        """Get the underlying agent instance.

        :returns: The agent instance.
        """
        ...

    async def generate_response(self, input_data: T) -> R:
        """Send a request to the agent provider.

        :param data: The input data for the request.
        :returns: The response from the agent provider.
        """
        ...


class InstructionsReader(Protocol):
    """Protocol for reading agent instructions.

    Implementations of this protocol provide a way to read instructions
    for agents from various sources (files, databases, APIs, etc.).

    Example:
        Implement a custom instructions reader::

            from agent_feng.core.abc import InstructionsReader

            class MyInstructionsReader:
                def read_instructions(self, agent_name: str) -> str:
                    return "Be helpful and concise."
    """

    def read_instructions(self, agent_name: str) -> str:
        """Read instructions for the given agent name.

        :param agent_name: The name of the agent.
        :returns: The instructions as a single string.
        :raises InstructionsReaderError: If instructions cannot be read.
        """
        ...
