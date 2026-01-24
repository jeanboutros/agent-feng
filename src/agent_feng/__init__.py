"""Agent Feng - AI application with pydantic-ai and MCP servers.

This package provides an AI agent application built with pydantic-ai
for structured AI interactions and MCP (Model Context Protocol) for
server integrations.

Example:
    Run the application::

        python -m agent_feng
        # or
        agent-feng
"""

from __future__ import annotations


def main() -> None:
    """Entry point for the console script.

    This function imports and delegates to the actual main function
    to avoid circular import issues when running as a module.

    Example:
        Called via console script::

            agent-feng
    """
    from agent_feng.__main__ import main as _main

    _main()


__all__ = ["main"]
