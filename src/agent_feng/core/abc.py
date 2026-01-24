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
