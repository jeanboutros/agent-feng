import logging
from typing import Literal, Self
import httpx

from agent_feng.core.abc import WebSearcher
from agent_feng.domain.brave_search import (
    BraveNewsSearchApiResponse,
    NewsSearchApiResponse,
)
from agent_feng.infrastructure.logging import get_main_logger


HttpHeaderType = dict[str, str] | None
HttpDictType = dict[str, str | int | float] | None


class WebClient:
    """Base web client class."""

    _BASE_URL = ""
    _HEADERS = {"user-agent": "agent-feng/0.0.1"}
    _TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
    _TRANSPORTS = {"https://": httpx.AsyncHTTPTransport()}
    _LOGGER = get_main_logger().getChild("WebClient")

    def __init__(self) -> None:
        """Initialize the web client with an HTTP client instance."""
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            http2=True,
            headers=self._HEADERS,
            timeout=self._TIMEOUT,
            mounts=self._TRANSPORTS,
            event_hooks={
                "request": [self._log_request],
                "response": [self._log_response],
            },
        )

    async def _log_response(self, response: httpx.Response) -> None:
        """Log the HTTP response details."""
        self._LOGGER.info(f"Response: {response.status_code} for {response.url}")
        self._LOGGER.debug(f"Headers: {response.headers}")

    async def _log_request(self, request: httpx.Request) -> None:
        """Log the HTTP request details."""
        self._LOGGER.info(f"Request: {request.method} {request.url}")
        self._LOGGER.debug(f"Headers: {request.headers}")
        if request.content:
            self._LOGGER.debug(f"Content: {request.content[0:100]}...")

    async def aclose(self) -> None:
        """Close the HTTP client and cleanup resources."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager and cleanup resources."""
        await self.aclose()

    async def get(
        self,
        endpoint: str,
        params: HttpDictType = None,
        headers: HttpHeaderType = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Perform a GET request to the specified endpoint.

        :param endpoint: The API endpoint to call.
        :param params: Query parameters for the request.
        :param headers: Headers for the request.
        :param raise_for_status: Whether to raise an exception for HTTP errors.
        :return: The response object.
        """
        url = f"{self._BASE_URL}{endpoint}"

        response = await self._client.get(url, params=params, headers=headers)
        if raise_for_status:
            response.raise_for_status()
        return response

    @property
    def logger(self) -> logging.Logger:
        """Get the logger for the web client."""
        return self._LOGGER


class BraveSearchClient(WebClient, WebSearcher):
    """Client for Brave Search API."""

    _BASE_URL = "https://api.search.brave.com"
    _HEADERS = {
        **WebClient._HEADERS.copy(),
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }
    _search_lang = Literal["ar", "zh-hans", "en", "fr"]
    _country = Literal[
        "ALL", "AR", "AU", "CA", "FR", "HK", "JP", "CN", "TW", "GB", "US"
    ]
    _safesearch = Literal["off", "moderate", "strict"]
    _freshness = (
        Literal["pd", "pw", "pm", "py"] | str
    )  # YYYY-MM-DDtoYYYY-MM-DD timeframe is also supported by specifying the date range e.g. 2022-04-01to2022-07-30

    def __init__(self, api_key: str) -> None:
        super().__init__()
        self._headers = {**self._HEADERS.copy(), "X-Subscription-Token": api_key}

    async def search_news(
        self,
        query: str,
        search_lang: _search_lang = "en",
        country: _country = "ALL",
        safesearch: _safesearch = "strict",
        freshness: _freshness = "pd",
        limit: int = 30,
    ) -> httpx.Response:
        """Perform a search query using Brave Search API.

        :param query: The search query string.
        :param limit: The number of search results to return.
        :return: The response object.
        """
        endpoint = "/res/v1/news/search"
        params: HttpDictType = {
            "q": query,
            "count": limit,
            "format": "json",
            "search_lang": search_lang,
            "country": country,
            "safesearch": safesearch,
            "freshness": freshness,
        }
        response = await self.get(endpoint, params=params, headers=self._headers)

        self.logger.debug("Brave News Search Response: %s", response.json())
        return response

    async def search(
        self,
        query: str,
        num_results: int = 10,
        get_last_n_hours: int = 24,
    ) -> BraveNewsSearchApiResponse:
        """Perform a web search for the given query.

        :param query: The search query string.
        :param num_results: The number of results to return.
        :param get_last_n_hours: The number of past hours to limit the search to (max 24).
        :returns: A list of search result snippets.
        """
        if get_last_n_hours > 0 and get_last_n_hours <= 24:
            from datetime import datetime, timedelta

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=get_last_n_hours)
            freshness_str = (
                f"{start_time.date().isoformat()}to{end_time.date().isoformat()}"
            )
            self.logger.debug(
                "Setting freshness to last %d hours: %s",
                get_last_n_hours,
                freshness_str,
            )
        else:
            freshness_str = "pd"  # past day

        response = await self.search_news(
            query=query, limit=num_results, freshness=freshness_str
        )

        parsed_response = BraveNewsSearchApiResponse.model_validate_json(response.text)
        return parsed_response
