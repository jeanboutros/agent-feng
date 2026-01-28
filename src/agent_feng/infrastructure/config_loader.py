"""YAML configuration loader for Agent Feng.

This module provides a concrete implementation of the ConfigLoader protocol
that reads configuration from YAML files in the project's config directory.

Example:
    Load configuration from the default config file::

        from agent_feng.infrastructure.config_loader import YamlConfigLoader
        from pathlib import Path

        config_dir = Path("config")
        loader = YamlConfigLoader(config_dir / "config.yaml")
        config = loader.load_config()
        provider = loader.get_property("ai.provider", default_value="openai")
"""

from __future__ import annotations

import functools
import logging
from functools import reduce
from pathlib import Path
from typing import Any

import yaml

from agent_feng.core.abc import ConfigLoader
from agent_feng.core.exceptions import ConfigFileError

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class YamlConfigLoader(ConfigLoader):
    """Configuration loader that reads from YAML files.

    This class implements the ConfigLoader protocol, providing methods to
    load and query configuration from YAML files. Configuration values
    can be accessed using dot-notation keys.

    :param config_path: Path to the YAML configuration file.

    Example:
        Basic usage::

            from pathlib import Path
            from agent_feng.infrastructure.config_loader import YamlConfigLoader

            loader = YamlConfigLoader(Path("config/config.yaml"))
            config = loader.load_config()

            # Get a simple value
            app_name = loader.get_property("application.name")

            # Get a nested value with default
            port = loader.get_property("api.port", default_value=8000, cast_type=int)

        Handling missing configuration::

            try:
                loader = YamlConfigLoader(Path("nonexistent.yaml"))
                loader.load_config()
            except ConfigFileError as e:
                print(f"Failed to load config: {e}")
    """

    def __init__(self, config_path: Path) -> None:
        """Initialize the YAML configuration loader.

        :param config_path: Path to the YAML configuration file.
        """
        self._config_path = config_path
        self._config: dict[str, Any] | None = None

    @property
    def config_path(self) -> Path:
        """Get the path to the configuration file.

        :returns: The configuration file path.

        Example:
            Access the config path::

                loader = YamlConfigLoader(Path("config/config.yaml"))
                print(f"Loading from: {loader.config_path}")
        """
        return self._config_path

    def load_config(self) -> dict[str, Any]:
        """Load configuration from the YAML file.

        Reads and parses the YAML file, caching the result for subsequent
        calls. If the file has already been loaded, returns the cached
        configuration.

        :returns: The loaded configuration as a dictionary.
        :raises ConfigFileError: If the file cannot be read or parsed.

        Example:
            Load and access configuration::

                loader = YamlConfigLoader(Path("config/config.yaml"))
                config = loader.load_config()
                print(config["application"]["name"])
        """
        if self._config is not None:
            return self._config

        if not self._config_path.exists():
            raise ConfigFileError(
                str(self._config_path),
                "Configuration file does not exist",
            )

        if not self._config_path.is_file():
            raise ConfigFileError(
                str(self._config_path),
                "Path is not a file",
            )

        try:
            with self._config_path.open(mode="r", encoding="utf-8") as config_file:
                content = yaml.safe_load(config_file)
                if content is None:
                    content = {}
                if not isinstance(content, dict):
                    raise ConfigFileError(
                        str(self._config_path),
                        "Configuration file must contain a YAML mapping at root level",
                    )
                self._config = content
                logger.debug("Loaded configuration from %s", self._config_path)
                return self._config
        except yaml.YAMLError as e:
            raise ConfigFileError(
                str(self._config_path),
                f"Invalid YAML syntax: {e}",
            ) from e
        except OSError as e:
            raise ConfigFileError(
                str(self._config_path),
                f"Failed to read file: {e}",
            ) from e

    @functools.lru_cache(maxsize=20)
    def get_property(
        self,
        key: str,
        default_value: Any = None,
        cast_type: type[Any] = str,
    ) -> Any:
        """Get a configuration property by dot-notation key.

        Supports nested key access using dot notation (e.g., "ai.provider").
        If the key is not found, returns the default value. The value is
        cast to the specified type.

        :param key: The dot-notation configuration key.
        :param default_value: The default value if the key is not found.
        :param cast_type: The type to cast the value to.
        :returns: The configuration value cast to the specified type.
        :raises ConfigFileError: If configuration has not been loaded.

        Example:
            Get typed configuration values::

                loader = YamlConfigLoader(Path("config/config.yaml"))
                loader.load_config()

                # String value (default)
                name = loader.get_property("application.name")

                # Integer value
                port = loader.get_property("api.port", default_value=8000, cast_type=int)

                # Boolean value
                enabled = loader.get_property("api.enabled", default_value=False, cast_type=bool)

                # Nested access
                provider = loader.get_property("ai.provider", default_value="openai")
        """
        if self._config is None:
            self.load_config()

        keys = key.split(".")
        try:
            value = reduce(lambda d, k: d[k], keys, self._config)
        except (KeyError, TypeError):
            logger.debug(
                "Configuration key '%s' not found, using default: %s",
                key,
                default_value,
            )
            return default_value

        if value is None:
            return default_value

        if cast_type is str or cast_type is Any:
            return value

        # Handle boolean casting specially
        if cast_type is bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)

        try:
            return cast_type(value)
        except (ValueError, TypeError):
            logger.warning(
                "Failed to cast '%s' to %s, returning as-is",
                key,
                cast_type.__name__,
            )
            return value

    def reload(self) -> dict[str, Any]:
        """Reload configuration from the YAML file.

        Forces a fresh read of the configuration file, discarding any
        cached values.

        :returns: The reloaded configuration as a dictionary.
        :raises ConfigFileError: If the file cannot be read or parsed.

        Example:
            Reload configuration after external changes::

                loader = YamlConfigLoader(Path("config/config.yaml"))
                loader.load_config()

                # ... configuration file is modified externally ...

                config = loader.reload()
        """
        self._config = None
        return self.load_config()

    def __repr__(self) -> str:
        """Return a string representation of the loader.

        :returns: String representation including the config path.

        Example:
            Print loader info::

                loader = YamlConfigLoader(Path("config/config.yaml"))
                print(repr(loader))  # YamlConfigLoader(config_path=config/config.yaml)
        """
        return f"YamlConfigLoader(config_path={self._config_path})"
