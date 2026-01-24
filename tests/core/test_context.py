"""Tests for the application context module.

This module contains tests for context creation, environment loading,
and validation logic.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from agent_feng.core.context import (
    ApplicationContext,
    Environment,
    LogLevel,
    _get_environment,
    _get_log_level,
    _get_project_root,
    _load_env_file,
    create_application_context,
)


class TestGetProjectRoot:
    """Tests for _get_project_root function."""

    def test_get_project_root_returns_path(self) -> None:
        """Test that project root is returned as a Path."""
        root = _get_project_root()

        assert isinstance(root, Path)
        assert root.exists()

    def test_get_project_root_contains_pyproject(self) -> None:
        """Test that project root contains pyproject.toml."""
        root = _get_project_root()

        assert (root / "pyproject.toml").exists()


class TestLoadEnvFile:
    """Tests for _load_env_file function."""

    def test_load_env_file_returns_true_when_exists(self, tmp_path: Path) -> None:
        """Test that True is returned when .env file exists."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test")

        result = _load_env_file(tmp_path, raise_on_missing=False)

        assert result is True

    def test_load_env_file_returns_false_when_missing(self, tmp_path: Path) -> None:
        """Test that False is returned when .env file is missing and not raising."""
        result = _load_env_file(tmp_path, raise_on_missing=False)

        assert result is False

    def test_load_env_file_raises_when_missing_and_required(
        self, tmp_path: Path
    ) -> None:
        """Test that FileNotFoundError is raised when .env is missing and required."""
        with pytest.raises(FileNotFoundError, match="Environment file not found"):
            _load_env_file(tmp_path, raise_on_missing=True)


class TestGetLogLevel:
    """Tests for _get_log_level function."""

    def test_get_log_level_returns_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that default log level is returned when not set."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)

        result = _get_log_level()

        assert result == LogLevel.INFO

    def test_get_log_level_reads_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that log level is read from environment variable."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        result = _get_log_level()

        assert result == LogLevel.DEBUG

    def test_get_log_level_handles_invalid_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that invalid log level falls back to default."""
        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        result = _get_log_level()

        assert result == LogLevel.INFO

    def test_get_log_level_case_insensitive(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that log level parsing is case insensitive."""
        monkeypatch.setenv("LOG_LEVEL", "warning")

        result = _get_log_level()

        assert result == LogLevel.WARNING


class TestGetEnvironment:
    """Tests for _get_environment function."""

    def test_get_environment_returns_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that default environment is returned when not set."""
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        result = _get_environment()

        assert result == Environment.DEVELOPMENT

    def test_get_environment_reads_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that environment is read from environment variable."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        result = _get_environment()

        assert result == Environment.PRODUCTION

    def test_get_environment_handles_invalid_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that invalid environment falls back to default."""
        monkeypatch.setenv("ENVIRONMENT", "invalid")

        result = _get_environment()

        assert result == Environment.DEVELOPMENT


class TestApplicationContext:
    """Tests for ApplicationContext dataclass."""

    def test_application_context_is_immutable(self, tmp_path: Path) -> None:
        """Test that ApplicationContext is frozen (immutable)."""
        # Create a valid project root
        (tmp_path / "pyproject.toml").touch()

        context = ApplicationContext(
            project_root=tmp_path,
            environment=Environment.DEVELOPMENT,
            log_level=LogLevel.INFO,
            logger=logging.getLogger("test"),
        )

        with pytest.raises(AttributeError):
            context.environment = Environment.PRODUCTION  # type: ignore[misc]

    def test_application_context_validates_project_root(self) -> None:
        """Test that ApplicationContext validates project_root exists."""
        non_existent = Path("/this/path/does/not/exist")

        with pytest.raises(ValueError, match="Project root does not exist"):
            ApplicationContext(
                project_root=non_existent,
                environment=Environment.DEVELOPMENT,
                log_level=LogLevel.INFO,
                logger=logging.getLogger("test"),
            )


class TestCreateApplicationContext:
    """Tests for create_application_context factory function."""

    def test_create_application_context_returns_context(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that create_application_context returns an ApplicationContext."""
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        monkeypatch.setenv("ENVIRONMENT", "development")

        context = create_application_context(raise_on_missing_env=False)

        assert isinstance(context, ApplicationContext)
        assert context.log_level == LogLevel.WARNING
        assert context.environment == Environment.DEVELOPMENT
        assert context.project_root.exists()
        assert isinstance(context.logger, logging.Logger)

    def test_create_application_context_with_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that create_application_context uses defaults when env vars not set."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)

        context = create_application_context(raise_on_missing_env=False)

        assert context.log_level == LogLevel.INFO
        assert context.environment == Environment.DEVELOPMENT
