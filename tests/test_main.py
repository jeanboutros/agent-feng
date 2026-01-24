"""Tests for the application entry point.

This module contains tests for the composition root and startup logic.
"""

from __future__ import annotations

import pytest

from agent_feng.__main__ import async_main
from agent_feng.core.context import create_application_context


class TestAsyncMain:
    """Tests for the async main entry point."""

    async def test_async_main_returns_zero_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that async_main returns 0 on successful startup."""
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        monkeypatch.setenv("ENVIRONMENT", "development")

        context = create_application_context(raise_on_missing_env=False)
        exit_code = await async_main(context)

        assert exit_code == 0
