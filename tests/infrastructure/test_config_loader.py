"""Tests for YamlConfigLoader.

This module contains unit tests for the YAML configuration loader
implementation.
"""

from __future__ import annotations

import asyncio
from json import load
from pathlib import Path
from textwrap import dedent

import pytest

from agent_feng.core.exceptions import ConfigFileError
from agent_feng.infrastructure.config_loader import YamlConfigLoader


class TestYamlConfigLoaderInit:
    """Tests for YamlConfigLoader initialization."""

    def test_init_stores_config_path(self, tmp_path: Path) -> None:
        """Config path is stored correctly."""
        config_path = tmp_path / "config.yaml"
        loader = YamlConfigLoader(config_path)
        assert loader.config_path == config_path

    def test_repr_shows_config_path(self, tmp_path: Path) -> None:
        """String representation includes config path."""
        config_path = tmp_path / "config.yaml"
        loader = YamlConfigLoader(config_path)
        assert str(config_path) in repr(loader)


class TestYamlConfigLoaderLoadConfig:
    """Tests for load_config method."""

    async def test_load_config_returns_dict(self, tmp_path: Path) -> None:
        """load_config returns a dictionary."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("key: value\n", encoding="utf-8")

        loader = YamlConfigLoader(config_path)
        config = await loader.load_config()

        assert isinstance(config, dict)
        assert config["key"] == "value"

    async def test_load_config_caches_result(self, tmp_path: Path) -> None:
        """Subsequent calls return cached configuration."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("key: value\n", encoding="utf-8")

        loader = YamlConfigLoader(config_path)
        config1 = await loader.load_config()
        config2 = await loader.load_config()

        assert config1 is config2

    async def test_get_property_caches_result(self, tmp_path: Path) -> None:
        """Subsequent calls return cached property."""

        config_path = tmp_path / "config.yaml"
        await asyncio.to_thread(
            config_path.write_text, "key: value\n", encoding="utf-8"
        )

        loader = YamlConfigLoader(config_path)

        # Get property first time
        value_1 = await loader.get_property("key")

        # Modify the config file and reload the new configuration
        await asyncio.to_thread(
            config_path.write_text, "key: new_value\n", encoding="utf-8"
        )
        await loader.reload()

        # Get property second time (should be cached)
        value_2 = await loader.get_property("key")

        assert value_1 == value_2
        assert value_2 == "value"

        # Clear the cache and get property again (should reflect new value)
        loader.get_property.cache_clear()
        value_3 = await loader.get_property("key")
        assert value_3 == "new_value"

    async def test_load_config_handles_nested_structure(self, tmp_path: Path) -> None:
        """Nested YAML structures are loaded correctly."""
        config_path = tmp_path / "config.yaml"
        config_content = dedent("""
            application:
              name: Test App
              version: 1.0.0
            database:
              host: localhost
              port: 5432
        """).strip()
        await asyncio.to_thread(
            config_path.write_text, config_content, encoding="utf-8"
        )

        loader = YamlConfigLoader(config_path)
        config = await loader.load_config()

        assert config["application"]["name"] == "Test App"
        assert config["database"]["port"] == 5432

    async def test_load_config_raises_for_missing_file(self, tmp_path: Path) -> None:
        """ConfigFileError raised for nonexistent file."""
        config_path = tmp_path / "nonexistent.yaml"
        loader = YamlConfigLoader(config_path)

        with pytest.raises(ConfigFileError) as exc_info:
            await loader.load_config()

        assert "does not exist" in str(exc_info.value)

    async def test_load_config_raises_for_directory(self, tmp_path: Path) -> None:
        """ConfigFileError raised when path is a directory."""
        loader = YamlConfigLoader(tmp_path)

        with pytest.raises(ConfigFileError) as exc_info:
            await loader.load_config()

        assert "not a file" in str(exc_info.value)

    async def test_load_config_raises_for_invalid_yaml(self, tmp_path: Path) -> None:
        """ConfigFileError raised for invalid YAML syntax."""
        config_path = tmp_path / "config.yaml"
        await asyncio.to_thread(
            config_path.write_text, "invalid: yaml: syntax: :\n", encoding="utf-8"
        )

        loader = YamlConfigLoader(config_path)

        with pytest.raises(ConfigFileError) as exc_info:
            await loader.load_config()

        assert "Invalid YAML syntax" in str(exc_info.value)

    async def test_load_config_raises_for_non_dict_root(self, tmp_path: Path) -> None:
        """ConfigFileError raised when root is not a mapping."""
        config_path = tmp_path / "config.yaml"
        await asyncio.to_thread(
            config_path.write_text, "- item1\n- item2\n", encoding="utf-8"
        )

        loader = YamlConfigLoader(config_path)

        with pytest.raises(ConfigFileError) as exc_info:
            await loader.load_config()

        assert "mapping at root level" in str(exc_info.value)

    async def test_load_config_handles_empty_file(self, tmp_path: Path) -> None:
        """Empty YAML file returns empty dict."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("", encoding="utf-8")

        loader = YamlConfigLoader(config_path)
        config = await loader.load_config()

        assert config == {}


class TestYamlConfigLoaderGetProperty:
    """Tests for get_property method."""

    @pytest.fixture
    async def loader_with_config(self, tmp_path: Path) -> YamlConfigLoader:
        """Create a loader with a sample configuration."""
        config_path = tmp_path / "config.yaml"
        config_content = dedent("""
            application:
              name: Test App
              version: 1.0.0
            api:
              enabled: true
              port: 8000
              host: localhost
            feature_flags:
              debug: false
              experimental: null
        """).strip()
        config_path.write_text(config_content, encoding="utf-8")

        loader = YamlConfigLoader(config_path)
        await loader.load_config()
        return loader

    async def test_get_property_simple_key(
        self, loader_with_config: YamlConfigLoader
    ) -> None:
        """Simple dot-notation key retrieves value."""
        name = await loader_with_config.get_property("application.name")
        assert name == "Test App"

    async def test_get_property_nested_key(
        self, loader_with_config: YamlConfigLoader
    ) -> None:
        """Nested dot-notation key retrieves value."""
        port = await loader_with_config.get_property("api.port", cast_type=int)
        assert port == 8000
        assert isinstance(port, int)

    async def test_get_property_returns_default_for_missing(
        self, loader_with_config: YamlConfigLoader
    ) -> None:
        """Default value returned for missing key."""
        value = await loader_with_config.get_property(
            "nonexistent.key", default_value="default"
        )
        assert value == "default"

    async def test_get_property_returns_default_for_null_value(
        self, loader_with_config: YamlConfigLoader
    ) -> None:
        """Default value returned for null YAML value."""
        value = await loader_with_config.get_property(
            "feature_flags.experimental", default_value="fallback"
        )
        assert value == "fallback"

    async def test_get_property_casts_to_int(
        self, loader_with_config: YamlConfigLoader
    ) -> None:
        """Value is cast to integer."""
        port = await loader_with_config.get_property("api.port", cast_type=int)
        assert isinstance(port, int)
        assert port == 8000

    async def test_get_property_casts_to_bool_true(
        self, loader_with_config: YamlConfigLoader
    ) -> None:
        """Boolean true value is handled correctly."""
        enabled = await loader_with_config.get_property("api.enabled", cast_type=bool)
        assert enabled is True

    async def test_get_property_casts_to_bool_false(
        self, loader_with_config: YamlConfigLoader
    ) -> None:
        """Boolean false value is handled correctly."""
        debug = await loader_with_config.get_property(
            "feature_flags.debug", cast_type=bool
        )
        assert debug is False

    async def test_get_property_raises_when_not_loaded(self, tmp_path: Path) -> None:
        """ConfigFileError raised when accessing property before loading."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("key: value\n", encoding="utf-8")

        loader = YamlConfigLoader(config_path)

        with pytest.raises(ConfigFileError) as exc_info:
            await loader.get_property("key")

        assert "Call load_config() first" in str(exc_info.value)


class TestYamlConfigLoaderReload:
    """Tests for reload method."""

    async def test_reload_returns_fresh_config(self, tmp_path: Path) -> None:
        """Reload returns fresh configuration."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("key: value1\n", encoding="utf-8")

        loader = YamlConfigLoader(config_path)
        config1 = await loader.load_config()
        assert config1["key"] == "value1"

        config_path.write_text("key: value2\n", encoding="utf-8")
        config2 = await loader.reload()
        assert config2["key"] == "value2"
        assert config1 is not config2
