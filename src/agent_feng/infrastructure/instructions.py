"""Instructions reader implementations for Agent Feng.

This module provides implementations for reading agent instructions
from various sources. Currently supports file-based instructions
stored as JSON arrays of strings.

Example:
    Read instructions for an agent::

        from agent_feng.infrastructure.instructions import InstructionsFileReader

        reader = InstructionsFileReader(context)
        instructions = reader.read_instructions("stocks_news")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from agent_feng.core.context import ApplicationContext
from agent_feng.core.exceptions import InstructionsReaderError


class InstructionsFileReader:
    """File-based instructions reader.

    Reads agent instructions from JSON files in the config/instructions directory.
    Files must be named: instructions_<agent_name>_<YYYYMMDDTHHmmss>.json
    The latest file (by timestamp) is used.

    :param context: Application context with project root and logger.

    Example:
        Read instructions::

            reader = InstructionsFileReader(context)
            instructions = reader.read_instructions("stocks_news")
    """

    def __init__(self, context: ApplicationContext) -> None:
        self._context = context
        self._logger = context.logger.getChild("InstructionsFileReader")

    def _get_instructions_file(self, agent_name: str) -> Path:
        """Find the latest instructions file for the given agent.

        :param agent_name: The name of the agent.
        :returns: Path to the latest instructions file.
        :raises InstructionsReaderError: If no instructions file is found.
        """
        config_path = self._context.project_root / "config" / "instructions"
        self._logger.debug("Looking for instructions in %s", config_path)

        if not config_path.exists():
            msg = f"Instructions directory not found: {config_path}"
            self._logger.error(msg)
            raise InstructionsReaderError(agent_name, msg)

        instruction_files = sorted(
            config_path.glob(f"instructions_{agent_name}_*.json"),
            reverse=True,
        )

        if not instruction_files:
            msg = f"No instructions file found for agent '{agent_name}'"
            self._logger.error(msg)
            raise InstructionsReaderError(agent_name, msg)

        latest_file = instruction_files[0]
        self._logger.info("Using instructions file: %s", latest_file.name)
        return latest_file

    def _validate_instructions_format(
        self, instructions_lines: Any, agent_name: str
    ) -> list[str]:
        """Validate the format of the instructions.

        :param instructions_lines: The instructions loaded from the file.
        :param agent_name: The agent name for error context.
        :returns: Validated list of instruction strings.
        :raises InstructionsReaderError: If the format is invalid.
        """
        if not isinstance(instructions_lines, list):
            msg = "Instructions file must contain a JSON array of strings"
            self._logger.error(msg)
            raise InstructionsReaderError(agent_name, msg)

        instructions_lines = cast(list[Any], instructions_lines)

        for i, line in enumerate(instructions_lines):
            if not isinstance(line, str):
                msg = (
                    f"Instruction line {i} must be a string, got {type(line).__name__}"
                )
                self._logger.error(msg)
                raise InstructionsReaderError(agent_name, msg)

        return cast(list[str], instructions_lines)

    def read_instructions(self, agent_name: str) -> str:
        """Read instructions from the latest instructions file for the given agent.

        :param agent_name: The name of the agent.
        :returns: The instructions as a single string.
        :raises InstructionsReaderError: If instructions cannot be read.

        Example:
            Read stocks news agent instructions::

                instructions = reader.read_instructions("stocks_news")
        """
        instructions_file = self._get_instructions_file(agent_name)

        try:
            with open(instructions_file, "rt", encoding="utf-8") as f:
                instructions_lines = json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in instructions file: {e}"
            self._logger.error(msg)
            raise InstructionsReaderError(agent_name, msg) from e

        instructions_lines = self._validate_instructions_format(
            instructions_lines, agent_name
        )

        instructions = "\n".join(instructions_lines)

        self._logger.debug(
            "Read %d lines of instructions for agent '%s'",
            len(instructions_lines),
            agent_name,
        )

        return instructions
