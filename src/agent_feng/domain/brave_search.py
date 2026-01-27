from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

"""Brave Search API response models for news search.

This module contains Pydantic models for parsing and validating
responses from the Brave News Search API.

Example
-------
>>> from agent_feng.domain.brave_search import NewsSearchApiResponse
>>> response = NewsSearchApiResponse(
...     query=Query(original="python programming"),
...     results=[
...         NewsResult(
...             title="Python 3.14 Released",
...             url="https://example.com/news/python-314"
...         )
...     ]
... )
>>> response.type
'news'
"""


class SearchOperators(BaseModel):
    """Search operators applied to a query.

    :ivar applied: Whether search operators were applied to the query.
    :ivar cleaned_query: The query after search operators have been processed.
    :ivar sites: List of site domains extracted from site: operators.

    Example
    -------
    >>> operators = SearchOperators(applied=True, sites=["example.com"])
    >>> operators.applied
    True
    """

    applied: bool = Field(
        default=False,
        description="Whether search operators were applied to the query.",
    )
    cleaned_query: str | None = Field(
        default=None,
        description="The query after search operators have been processed.",
    )
    sites: list[str] | None = Field(
        default=None,
        description="List of site domains extracted from site: operators.",
    )


class BaseQuery(BaseModel):
    """Base model for query information.

    This serves as a base class for query-related models.

    Example
    -------
    >>> base_query = BaseQuery(original="python programming")
    >>> isinstance(base_query, BaseModel)
    True
    """

    original: str = Field(
        description="The original query that was requested.",
    )


class Query(BaseQuery):
    """Query information from the search request.

    :ivar original: The original query that was requested.
    :ivar altered: The altered query by the spellchecker.
    :ivar cleaned: The cleaned normalized query by the spellchecker.
    :ivar spellcheck_off: Whether the spellchecker is enabled or disabled.
    :ivar show_strict_warning: True if lack of results is due to strict safesearch.
    :ivar search_operators: Search operators applied to the query.

    Example
    -------
    >>> query = Query(original="pythn programming", altered="python programming")
    >>> query.original
    'python programming'
    """

    altered: str | None = Field(
        default=None,
        description="The altered query by the spellchecker. This is the query that is used to search if any.",
    )
    cleaned: str | None = Field(
        default=None,
        description="The cleaned normalized query by the spellchecker. This is the query that is used to search if any.",
    )
    spellcheck_off: bool | None = Field(
        default=None,
        description="Whether the spellchecker is enabled or disabled.",
    )
    show_strict_warning: bool | None = Field(
        default=None,
        description="The value is true if the lack of results is due to a strict safesearch setting.",
    )
    search_operators: SearchOperators | None = Field(
        default=None,
        description="Search operators applied to the query.",
    )


class MetaUrl(BaseModel):
    """Aggregated information on a URL.

    :ivar scheme: The protocol scheme extracted from the URL.
    :ivar netloc: The network location part extracted from the URL.
    :ivar hostname: The lowercased domain name extracted from the URL.
    :ivar favicon: The favicon used for the URL.
    :ivar path: The hierarchical path of the URL useful as a display string.

    Example
    -------
    >>> meta = MetaUrl(scheme="https", hostname="example.com", path="/news")
    >>> meta.scheme
    'https'
    """

    scheme: str | None = Field(
        default=None,
        description="The protocol scheme extracted from the URL.",
    )
    netloc: str | None = Field(
        default=None,
        description="The network location part extracted from the URL.",
    )
    hostname: str | None = Field(
        default=None,
        description="The lowercased domain name extracted from the URL.",
    )
    favicon: str | None = Field(
        default=None,
        description="The favicon used for the URL.",
    )
    path: str | None = Field(
        default=None,
        description="The hierarchical path of the URL useful as a display string.",
    )


class Thumbnail(BaseModel):
    """Thumbnail image for a news article.

    :ivar src: The served URL of the thumbnail associated with the news article.
    :ivar original: The original URL of the thumbnail associated with the news article.

    Example
    -------
    >>> thumb = Thumbnail(src="https://cdn.example.com/thumb.jpg")
    >>> thumb.src
    'https://cdn.example.com/thumb.jpg'
    """

    src: str = Field(
        description="The served URL of the thumbnail associated with the news article.",
    )
    original: str | None = Field(
        default=None,
        description="The original URL of the thumbnail associated with the news article.",
    )


class PostprocessedIcon(BaseModel):
    """Icon associated with a news result.

    :ivar href: The URL of the icon.
    :ivar sizes: The sizes of the icon.
    :ivar rel: The relationship of the icon.
    :ivar type: The MIME type of the icon.
    :ivar ext: The file extension of the icon.

    Example
    -------
    >>> icon = PostprocessedIcon(
    ...     href="https://example.com/icon.png",
    ...     sizes="32x32",
    ...     rel="icon",
    ...     type="image/png",
    ...     ext="png"
    ... )
    >>> icon.href
    'https://example.com/icon.png'
    """

    href: str = Field(description="The URL of the icon.")
    sizes: str | None = Field(description="The sizes of the icon.")
    rel: str | None = Field(description="The relationship of the icon.")
    type: str | None = Field(description="The MIME type of the icon.")
    ext: str | None = Field(description="The file extension of the icon.")


class BaseNewsResult(BaseModel):
    """Base model for a news search result.

    This serves as a base class for news result-related models.

    Example
    -------
    >>> base_result = BaseNewsResult(title="Sample News", url="https://example.com")
    >>> isinstance(base_result, BaseModel)
    True
    """

    title: str = Field(
        description="The title of the news article.",
    )
    url: str = Field(
        description="The source URL of the news article.",
    )
    description: str | None = Field(
        default=None,
        description="The description for the news article.",
    )
    page_fetched: str | None = Field(
        default=None,
        description="The ISO date time when the page was last fetched. Format: YYYY-MM-DDTHH:MM:SSZ.",
    )
    news_publish_date: str | None = Field(
        default=None,
        description="The ISO date time when the news article was published. Format: YYYY-MM-DDTHH:MM:SSZ.",
    )


class NewsResult(BaseNewsResult):
    """A single news search result.

    :ivar type: The type of news search API result. Always 'news_result'.
    :ivar title: The title of the news article.
    :ivar url: The source URL of the news article.
    :ivar description: The description for the news article.
    :ivar age: A human readable representation of the page age.
    :ivar page_age: The page age found from the source web page.
    :ivar page_fetched: The ISO date time when the page was last fetched.
    :ivar fetched_content_timestamp: The timestamp when the content was fetched.
    :ivar meta_url: Aggregated information on the URL.
    :ivar breaking: Whether the result includes breaking news.
    :ivar thumbnail: The thumbnail for the news article.
    :ivar extra_snippets: A list of extra alternate snippets.
    :ivar icons: Icons associated with the news result.

    Example
    -------
    >>> result = NewsResult(
    ...     title="Breaking: New Python Release",
    ...     url="https://example.com/python-news",
    ...     breaking=True
    ... )
    >>> result.title
    'Breaking: New Python Release'
    """

    type: str = Field(
        default="news_result",
        description="The type of news search API result. The value is always news_result.",
    )
    age: str | None = Field(
        default=None,
        description="A human readable representation of the page age.",
    )
    page_age: str | None = Field(
        default=None,
        description="The page age found from the source web page.",
    )
    fetched_content_timestamp: int | None = Field(
        default=None,
        description="The timestamp when the content was fetched.",
    )
    meta_url: MetaUrl | None = Field(
        default=None,
        description="Aggregated information on the URL associated with the news search result.",
    )
    breaking: bool | None = Field(
        default=None,
        description="Whether the result includes breaking news.",
    )
    thumbnail: Thumbnail | None = Field(
        default=None,
        description="The thumbnail for the news article.",
    )
    extra_snippets: list[str] | None = Field(
        default=None,
        description="A list of extra alternate snippets for the news search result.",
    )
    icons: list[PostprocessedIcon] | None = Field(
        default=None,
        description="Icons associated with the news result.",
    )


class BraveNewsSearchApiResponse(BaseModel):
    """Response from the Brave News Search API.

    :ivar type: The type of search response. Always 'news'.
    :ivar query: Query information from the search request.
    :ivar results: The list of news results for the given query.

    Example
    -------
    >>> response = NewsSearchApiResponse(
    ...     query=Query(original="artificial intelligence"),
    ...     results=[
    ...         NewsResult(
    ...             title="AI Breakthrough Announced",
    ...             url="https://example.com/ai-news"
    ...         )
    ...     ]
    ... )
    >>> response.type
    'news'
    >>> len(response.results)
    1
    """

    type: Literal["news"] = Field(
        default="news",
        description="The type of search response. Always 'news'.",
    )
    query: Query = Field(
        description="Query information from the search request.",
    )
    results: list[NewsResult] = Field(
        default_factory=list[NewsResult],
        description="The list of news results for the given query.",
    )


class NewsSearchApiResponse(BaseModel):
    """Generic response for the news search queries.

    :ivar type: The type of search response. Always 'news'.
    :ivar query: Query information from the search request.
    :ivar results: The list of news results for the given query.

    Example
    -------
    >>> response = NewsSearchApiResponse(
    ...     query=Query(original="artificial intelligence"),
    ...     results=[
    ...         NewsResult(
    ...             title="AI Breakthrough Announced",
    ...             url="https://example.com/ai-news"
    ...         )
    ...     ]
    ... )
    >>> response.type
    'news'
    >>> len(response.results)
    1
    """

    query: BaseQuery = Field(
        description="Query information from the search request.",
    )
    results: list[BaseNewsResult] = Field(
        default_factory=list[BaseNewsResult],
        description="The list of news results for the given query.",
    )
