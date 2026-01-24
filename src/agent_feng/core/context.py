"""Application context management for Agent Feng.

This module provides the ApplicationContext class and factory functions
for creating and managing application-wide context. The context is
immutable after creation and holds runtime configuration.

Design Decision:
    A frozen dataclass was chosen over NamedTuple, TypedDict, or Pydantic because:

    - **TypedDict**: Intended for external data structures (JSON, APIs). Context is
      internal. Also mutable with no validation enforcement.
    - **NamedTuple**: Immutable but lacks validation hooks and is awkward for
      optional fields with defaults.
    - **Pydantic**: Logger objects are not serializable. Adds overhead for internal
      value objects. Better suited for external API contracts.
    - **Frozen Dataclass**: Immutable, supports ``__post_init__`` validation, handles
      Logger objects cleanly, lightweight, and aligns with Clean Architecture
      value objects.

Example:
    Create and use application context::

        from agent_feng.core.context import create_application_context

        context = create_application_context()
        context.logger.info("Application started in %s", context.environment)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

from agent_feng.core.abc import Environment, LogLevel
from agent_feng.infrastructure.logging import configure_logging


# Sentinel value for detecting missing .env file
_ENV_FILE_NOT_FOUND: Final[str] = "__ENV_FILE_NOT_FOUND__"


def _get_project_root() -> Path:
    """Determine the project root directory.

    The project root is identified by traversing up from this file's location
    until we find a directory containing pyproject.toml.

    :returns: Absolute path to the project root.
    :raises FileNotFoundError: If project root cannot be determined.

    Example:
        Get project root::

            root = _get_project_root()
            config_path = root / "config" / "config.yaml"
    """
    current = Path(__file__).resolve()

    # Traverse up looking for pyproject.toml
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent

    # Fallback: assume 4 levels up from this file
    # src/agent_feng/core/context.py -> project root
    fallback = Path(__file__).resolve().parent.parent.parent.parent

    if fallback.exists():
        return fallback

    msg = "Could not determine project root directory"
    raise FileNotFoundError(msg)


def _load_env_file(
    project_root: Path,
    *,
    raise_on_missing: bool = True,
) -> bool:
    """Load environment variables from .env file.

    :param project_root: Path to the project root directory.
    :param raise_on_missing: If True, raise an error when .env file is missing.
    :returns: True if .env file was loaded, False otherwise.
    :raises FileNotFoundError: If .env file is missing and raise_on_missing is True.

    Example:
        Load environment with strict mode::

            _load_env_file(project_root, raise_on_missing=True)

        Load environment with fallback to defaults::

            loaded = _load_env_file(project_root, raise_on_missing=False)
            if not loaded:
                logger.warning("Using default configuration")
    """
    env_file = project_root / ".env"

    if not env_file.exists():
        if raise_on_missing:
            msg = f"Environment file not found: {env_file}"
            raise FileNotFoundError(msg)
        return False

    load_dotenv(env_file)
    return True


def _get_log_level(default: LogLevel = LogLevel.INFO) -> LogLevel:
    """Get the configured log level from environment.

    :param default: Default log level if not configured.
    :returns: The configured LogLevel.

    Example:
        Get log level::

            level = _get_log_level()
            configure_logging(level=level.value)
    """
    raw_level = os.getenv("LOG_LEVEL", default.value).upper()

    try:
        return LogLevel(raw_level)
    except ValueError:
        # Invalid level, return default
        return default


def _get_environment(default: Environment = Environment.DEVELOPMENT) -> Environment:
    """Get the configured environment from environment variables.

    :param default: Default environment if not configured.
    :returns: The configured Environment.

    Example:
        Get environment::

            env = _get_environment()
            if env == Environment.PRODUCTION:
                enable_monitoring()
    """
    raw_env = os.getenv("ENVIRONMENT", default.value).lower()

    try:
        return Environment(raw_env)
    except ValueError:
        # Invalid environment, return default
        return default


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Immutable application context holding runtime configuration.

    This class is a frozen dataclass, meaning all attributes are read-only
    after instantiation. It serves as a value object passed through the
    application to provide access to shared configuration.

    :param project_root: Absolute path to the project root directory.
    :param environment: Current deployment environment.
    :param log_level: Configured logging level.
    :param logger: Configured root logger instance.

    Example:
        Access context properties::

            context = create_application_context()
            context.logger.info("Running in %s", context.environment)
            config_path = context.project_root / "config" / "config.yaml"
    """

    project_root: Path
    environment: Environment
    log_level: LogLevel
    logger: logging.Logger = field(repr=False)

    def __post_init__(self) -> None:
        """Validate context after initialization.

        :raises ValueError: If project_root does not exist.
        """
        if not self.project_root.exists():
            msg = f"Project root does not exist: {self.project_root}"
            raise ValueError(msg)


def create_application_context(
    *,
    raise_on_missing_env: bool = False,
) -> ApplicationContext:
    """Factory function to create an ApplicationContext.

    This function performs all initialization steps in the correct order:
    1. Determine project root
    2. Load .env file
    3. Read configuration from environment
    4. Configure logging
    5. Create and return immutable context

    :param raise_on_missing_env: If True, raise error when .env file is missing.
    :returns: Fully initialized ApplicationContext.
    :raises FileNotFoundError: If project root cannot be found or .env is missing
        and raise_on_missing_env is True.

    Example:
        Create context with defaults::

            context = create_application_context()

        Create context with strict .env requirement::

            context = create_application_context(raise_on_missing_env=True)
    """
    # Step 1: Determine project root
    project_root = _get_project_root()

    # Step 2: Load environment file
    _load_env_file(project_root, raise_on_missing=raise_on_missing_env)

    # Step 3: Read configuration
    log_level = _get_log_level()
    environment = _get_environment()

    # Step 4: Configure logging
    logger = configure_logging(level=log_level.value, environment=environment.value)

    # Step 5: Create and return context
    return ApplicationContext(
        project_root=project_root,
        environment=environment,
        log_level=log_level,
        logger=logger,
    )
