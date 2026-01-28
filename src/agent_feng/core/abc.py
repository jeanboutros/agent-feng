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
from typing import Any, Protocol
from async_lru import alru_cache

from agent_feng.domain.brave_search import NewsSearchApiResponse


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


class ConfigLoader(Protocol):
    """Protocol for configuration loader implementations.

    Example:
        Implement a custom config loader::

            from agent_feng.core.abc import ConfigLoader

            class MyConfigLoader:
                ...
    """

    async def load_config(self) -> dict[str, Any]:
        """Load configuration from the given path.

        :param config_path: The path to the configuration file.
        :returns: The loaded configuration as a dictionary.
        """
        ...

    @alru_cache(maxsize=128)
    async def get_property[T](
        self, key: str, default_value: Any = None, cast_type: type[T] = str
    ) -> T:
        """Get a configuration property by key.

        :param key: The configuration key.
        :param default_value: The default value if the key is not found.
        :returns: The configuration value.
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


class WebSearcher(Protocol):
    """Protocol for web searcher implementations.

    Example:
        Implement a custom web searcher::

            from agent_feng.core.abc import WebSearcher

            class MyWebSearcher:
                ...
    """

    async def search(self, query: str, num_results: int = 10) -> NewsSearchApiResponse:
        """Perform a web search for the given query.

        :param query: The search query string.
        :param num_results: The number of results to return.
        :returns: A list of URLs as search results.
        """
        ...
