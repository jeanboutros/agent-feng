"""Stocks news service for orchestrating stock market news retrieval.

This module contains the StocksNewsService which orchestrates AI-powered
stock news analysis. It depends only on Core abstractions, following
Clean Architecture's dependency rule.

Example:
    Create and use the service::

        from agent_feng.application.stocks_news_service import StocksNewsService

        service = StocksNewsService(ai_provider=agent, context=context)
        response = await service.get_news("AAPL")
"""

from __future__ import annotations

from typing import Any

from agent_feng.core.abc import AgentProvider
from agent_feng.core.context import ApplicationContext


class StocksNewsService:
    """Service to orchestrate stock news retrieval and analysis.

    This service receives pre-constructed dependencies from the composition
    root and orchestrates AI-powered stock news interactions. It contains no
    knowledge of infrastructure implementations.

    :param ai_provider: Pre-configured AI provider (injected).
    :param context: Application context with logger and configuration.

    Example:
        Using the service::

            service = StocksNewsService(ai_provider=agent, context=context)
            news = await service.get_news("What's the latest on TSLA?")
    """

    def __init__(
        self,
        ai_provider: AgentProvider[Any, str, str],
        context: ApplicationContext,
    ) -> None:
        self._ai_provider = ai_provider
        self._context = context
        self._logger = context.logger.getChild("StocksNewsService")

    async def get_news(self, query: str) -> str:
        """Retrieve and analyze stock news based on query.

        :param query: The stock news query (e.g., ticker symbol or question).
        :returns: AI-generated analysis of relevant stock news.

        Example:
            Get stock news::

                news = await service.get_news("Latest AAPL earnings news")
        """
        self._logger.debug("Processing stock news query: %s", query[:50])
        response = await self._ai_provider.generate_response(query)
        self._logger.info("Generated stock news response successfully")
        return response
