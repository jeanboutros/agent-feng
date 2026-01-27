"""Domain models for Agent Feng.

This module contains the core domain entities and value objects that
represent the business concepts of the application.

Example:
    Domain models are imported and used by application services::

        from agent_feng.domain.models import AgentConfig
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class AgentDeps(BaseModel):
    """Dependencies passed to the AI agent at runtime.

    Contains contextual information to help the model produce accurate
    responses, including temporal boundaries and agent identity.

    :param agent_name: Unique identifier for this agent instance.
    :param current_datetime: Current UTC datetime when the agent runs.
    :param earliest_search_date: Oldest date for news search queries.
    :param search_lookback_hours: Hours to look back for recent news.
    :param target_regions: Geographic regions to focus news search on.
    :param output_format: Expected output format (e.g., 'json').
    :param max_news_items: Maximum number of news items to include in report.
    :param model_guidance: Additional instructions to improve model accuracy.

    Example:
        Creating agent dependencies::

            from datetime import datetime, timezone
            deps = AgentDeps(
                agent_name="feng_stocks_news_agent",
                target_regions=["US", "Asia", "Europe"],
            )
            print(deps.current_datetime_iso)
    """

    agent_name: str = Field(
        ...,
        description="Unique identifier for this agent instance",
    )
    current_datetime: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Current UTC datetime when the agent runs",
    )
    earliest_search_date: datetime | None = Field(
        default=None,
        description="Oldest date for news search queries (auto-calculated if not provided)",
    )
    search_lookback_hours: int = Field(
        default=24,
        description="Number of hours to look back for recent news",
    )
    target_regions: list[str] = Field(
        default_factory=lambda: ["US", "Global"],
        description="Geographic regions to focus news search on",
    )
    output_format: str = Field(
        default="json",
        description="Expected output format (e.g., 'json', 'markdown')",
    )
    max_news_items: int = Field(
        default=30,
        description="Maximum number of news items to include in report",
    )
    model_guidance: str = Field(
        default="",
        description="Additional instructions to improve model accuracy",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def calculate_earliest_search_date(self) -> "AgentDeps":
        """Calculate earliest_search_date if not provided."""
        if self.earliest_search_date is None:
            object.__setattr__(
                self,
                "earliest_search_date",
                self.current_datetime - timedelta(hours=self.search_lookback_hours),
            )
        return self

    @property
    def current_datetime_iso(self) -> str:
        """Current datetime in ISO 8601 format.

        Returns:
            str: ISO formatted datetime string.
        """
        return self.current_datetime.isoformat(sep="T", timespec="seconds")

    @property
    def earliest_search_date_iso(self) -> str:
        """Earliest search date in ISO 8601 format.

        Returns:
            str: ISO formatted datetime string.
        """
        if self.earliest_search_date is None:
            return ""
        return self.earliest_search_date.isoformat(sep="T", timespec="seconds")

    @property
    def regions_str(self) -> str:
        """Target regions as comma-separated string.

        Returns:
            str: Comma-separated list of regions.
        """
        return ", ".join(self.target_regions)


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
