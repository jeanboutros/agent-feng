"""Core module for Agent Feng.

This module contains foundational components used across the application,
including context management, configuration, and shared utilities.

Example:
    Import core components::

        from agent_feng.core import ApplicationContext, create_application_context
        from agent_feng.core import Environment, LogLevel
        from agent_feng.core import AgentFengError, ConfigurationError
"""

from __future__ import annotations

from agent_feng.core.abc import Environment, LogLevel
from agent_feng.core.context import ApplicationContext, create_application_context
from agent_feng.core.exceptions import (
    AgentFengError,
    AIProviderError,
    ConfigFileError,
    ConfigurationError,
    ContextError,
    EnvironmentConfigError,
    InfrastructureError,
    MCPError,
)

__all__ = [
    # Context
    "ApplicationContext",
    "create_application_context",
    # Enums
    "Environment",
    "LogLevel",
    # Exceptions
    "AgentFengError",
    "AIProviderError",
    "ConfigFileError",
    "ConfigurationError",
    "ContextError",
    "EnvironmentConfigError",
    "InfrastructureError",
    "MCPError",
]
