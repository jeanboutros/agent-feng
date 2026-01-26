"""Domain models for Agent Feng.

This module contains the core domain entities and value objects that
represent the business concepts of the application.

Example:
    Domain models are imported and used by application services::

        from agent_feng.domain.models import AgentConfig
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Sentiment(StrEnum):
    """Sentiment classification for stock news.

    Example:
        >>> sentiment = Sentiment.BULLISH
        >>> print(sentiment)
        'BULLISH'
    """

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class NewsSource(BaseModel):
    """A source where a news item was published.

    :param name: The name of the website or publication.
    :param url: The URL where the news can be found.

    Example:
        >>> source = NewsSource(name="Reuters", url="https://reuters.com/article/123")
        >>> source.name
        'Reuters'
    """

    name: str = Field(..., description="Name of the website or publication")
    url: HttpUrl = Field(..., description="URL where the news can be found")


class NewsItem(BaseModel):
    """A single news item with stock analysis.

    :param headline: Brief summary of the news.
    :param stock_ticker: The relevant stock symbol (e.g., AAPL, TSLA, MSFT).
    :param company_name: Full company name.
    :param sentiment: Sentiment classification for the stock.
    :param reasoning: Explanation for the sentiment classification.
    :param sources: List of sources where the news appears.
    :param published_at: The date and time when the news was published in UTC.
    :param retrieved_at: The date and time when the news was retrieved in UTC.

    Example:
        >>> from datetime import datetime, timezone
        >>> item = NewsItem(
        ...     headline="Apple announces record earnings",
        ...     stock_ticker="AAPL",
        ...     company_name="Apple Inc.",
        ...     sentiment=Sentiment.BULLISH,
        ...     reasoning="Strong earnings beat expectations",
        ...     sources=[NewsSource(name="Reuters", url="https://reuters.com/article/123")],
        ...     published_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        ...     retrieved_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        ... )
        >>> item.stock_ticker
        'AAPL'
    """

    headline: str = Field(..., description="Brief summary of the news")
    stock_ticker: str = Field(
        ..., description="The relevant stock symbol (e.g., AAPL, TSLA, MSFT)"
    )
    company_name: str = Field(..., description="Full company name")
    sentiment: Sentiment = Field(
        ..., description="Sentiment classification for the stock"
    )
    reasoning: str = Field(
        ..., description="Explanation for the sentiment classification"
    )
    sources: list[NewsSource] = Field(
        default_factory=list, description="List of sources where the news appears"
    )
    published_at: datetime = Field(
        ..., description="Date and time when the news was published in UTC"
    )
    retrieved_at: datetime = Field(
        ..., description="Date and time when the news was retrieved in UTC"
    )


class NewsAnalysisReport(BaseModel):
    """Complete news analysis report containing multiple news items.

    :param news_items: List of analyzed news items.
    :param summary: A summary of all the news.
    :param analysis: A final analysis on all the news.

    Example:
        >>> from datetime import datetime, timezone
        >>> report = NewsAnalysisReport(
        ...     news_items=[
        ...         NewsItem(
        ...             headline="Apple announces record earnings",
        ...             stock_ticker="AAPL",
        ...             company_name="Apple Inc.",
        ...             sentiment=Sentiment.BULLISH,
        ...             reasoning="Strong earnings beat expectations",
        ...             sources=[],
        ...             published_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        ...             retrieved_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        ...         )
        ...     ],
        ...     summary="Overall positive market sentiment",
        ...     analysis="Tech sector showing strong performance",
        ... )
        >>> len(report.news_items)
        1
    """

    news_items: list[NewsItem] = Field(
        default_factory=list[NewsItem], description="List of analyzed news items"
    )
    summary: str = Field(..., description="A summary of all the news")
    analysis: str = Field(..., description="A final analysis on all the news")
    analysis_generated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Date and time when the analysis was generated in UTC",
    )

    model_config = ConfigDict(
        validate_assignment=False,
        json_encoders={
            datetime: lambda v: v.isoformat(sep=" ", timespec="seconds"),
        },
    )
