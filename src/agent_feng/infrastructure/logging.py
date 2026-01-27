"""Logging configuration for Agent Feng.

This module provides logging setup utilities that are invoked exclusively
from the composition root. All library modules should use NullHandler.

Example:
    Configure logging at application startup::

        from agent_feng.infrastructure.logging import configure_logging
        configure_logging(level="INFO", environment="development")
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Literal

Environment = Literal["development", "production"]


class UTCFormatter(logging.Formatter):
    """Formatter that outputs timestamps in UTC with Zulu (Z) suffix."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Format time in UTC with Z suffix.

        :param record: The log record.
        :param datefmt: Date format string.
        :returns: Formatted timestamp in UTC with Z suffix.
        """
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            s = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        return f"{s}Z"

    converter = time.gmtime  # Use UTC instead of local time


def configure_logging(
    level: str = "INFO",
    environment: Environment = "development",
    datefmt: str = "%Y%m%dT%H%M%S",
) -> logging.Logger:
    """Configure the root PANPAN logger for the application.

    This function sets up the logging infrastructure with appropriate
    handlers and formatters based on the environment.

    :param level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    :param environment: The deployment environment.
    :returns: The configured root logger.

    Example:
        Configure logging for development::

            logger = configure_logging(level="DEBUG", environment="development")
            logger.info("Application started")
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create the root PANPAN logger
    logger = logging.getLogger("PANPAN")
    logger.setLevel(log_level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Format based on environment
    if environment == "production":
        # JSON-like format for production (easier to parse)
        formatter = UTCFormatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}',
            datefmt=datefmt,
        )
    else:
        # Human-readable format for development
        formatter = UTCFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt=datefmt,
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
    logger = logging.getLogger("PANPAN")


def get_main_logger() -> logging.Logger:
    """Get the main PANPAN logger.

    :returns: The main PANPAN logger instance.

    Example:
        Get the main logger::

            logger = get_main_logger()
            logger.info("Using the main logger")
    """
    return logging.getLogger("PANPAN")
