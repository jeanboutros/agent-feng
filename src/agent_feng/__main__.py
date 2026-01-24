"""Entry point and composition root for Agent Feng.

This module serves as the sole composition root for the application.
All dependency wiring, configuration loading, secrets injection,
and logging setup happens here.

Example:
    Run the application::

        python -m agent_feng
"""

from __future__ import annotations

import asyncio
import sys

from agent_feng.core import ApplicationContext, create_application_context


async def async_main(context: ApplicationContext) -> int:
    """Async entry point for the application.

    This function initializes all dependencies using the provided context
    and starts the application.

    :param context: The application context with configuration and logger.
    :returns: Exit code (0 for success, non-zero for failure).

    Example:
        Run the async main::

            context = create_application_context()
            exit_code = await async_main(context)
    """
    context.logger.info("Agent Feng starting up")
    context.logger.info("Environment: %s", context.environment.value)
    context.logger.info("Log level: %s", context.log_level.value)
    context.logger.info("Project root: %s", context.project_root)

    # TODO: Initialize application components here
    # - Load configuration from config/config.yaml
    # - Initialize MCP clients
    # - Initialize pydantic-ai agents
    # - Start FastAPI server (if enabled)

    context.logger.info("Agent Feng initialized successfully")

    return 0


def main() -> None:
    """Synchronous entry point wrapper.

    This function serves as the main entry point called by the console script.
    It creates the application context, wraps the async_main function,
    and handles the event loop.

    Example:
        Called via console script::

            agent-feng
    """
    # Create application context (composition root responsibility)
    context = create_application_context(raise_on_missing_env=False)

    exit_code = asyncio.run(async_main(context))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
