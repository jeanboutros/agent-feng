"""Tests for logging infrastructure.

This module contains tests for the logging configuration.
"""

from __future__ import annotations

import logging

import pytest

from agent_feng.infrastructure.logging import configure_logging


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_configure_logging_creates_panpan_logger(self) -> None:
        """Test that the PANPAN logger is created."""
        logger = configure_logging(level="INFO", environment="development")

        assert logger.name == "PANPAN"
        assert logger.level == logging.INFO

    def test_configure_logging_respects_level(self) -> None:
        """Test that the logging level is properly set."""
        logger = configure_logging(level="DEBUG", environment="development")

        assert logger.level == logging.DEBUG

    def test_configure_logging_has_console_handler(self) -> None:
        """Test that a console handler is attached."""
        logger = configure_logging(level="INFO", environment="development")

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_configure_logging_clears_existing_handlers(self) -> None:
        """Test that existing handlers are cleared on reconfiguration."""
        # Configure twice
        configure_logging(level="INFO", environment="development")
        logger = configure_logging(level="DEBUG", environment="development")

        # Should only have one handler, not two
        assert len(logger.handlers) == 1

    @pytest.mark.parametrize(
        "environment,expected_format_contains",
        [
            ("development", "|"),
            ("production", '"level"'),
        ],
    )
    def test_configure_logging_format_by_environment(
        self, environment: str, expected_format_contains: str
    ) -> None:
        """Test that format differs by environment."""
        logger = configure_logging(level="INFO", environment=environment)  # type: ignore[arg-type]

        formatter = logger.handlers[0].formatter
        assert formatter is not None
        assert expected_format_contains in formatter._fmt
