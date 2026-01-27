"""Entry point and composition root for Agent Feng.

This module serves as the sole composition root for the application.
All dependency wiring, configuration loading, secrets injection,
and logging setup happens here.

Example:
    Run the application::

        python -m agent_feng
"""

from __future__ import annotations

import asyncio
import sys

from agent_feng.core import ApplicationContext, create_application_context
from agent_feng.domain.models import AgentDeps, NewsAnalysisReport

from agent_feng.infrastructure.web_clients import BraveSearchClient


async def async_main(context: ApplicationContext) -> int:
    """Async entry point for the application.

    This function initializes all dependencies using the provided context
    and starts the application. This is the composition root where all
    dependency wiring occurs.

    :param context: The application context with configuration and logger.
    :returns: Exit code (0 for success, non-zero for failure).

    Example:
        Run the async main::

            context = create_application_context()
            exit_code = await async_main(context)
    """
    context.logger.info("Agent Feng starting up")
    context.logger.info("Environment: %s", context.environment.value)
    context.logger.info("Log level: %s", context.log_level.value)
    context.logger.info("Project root: %s", context.project_root)

    # =========================================================================
    # COMPOSITION ROOT: All dependency wiring happens here
    # =========================================================================

    # Import infrastructure implementations (only in composition root)
    from agent_feng.infrastructure.pydantic_ai_adapters import (
        ModelType,
        PydanticAIAgentAdapter,
        PydanticAIModelAdapter,
    )
    from agent_feng.infrastructure.instructions import InstructionsFileReader
    from agent_feng.application.stocks_news_service import StocksNewsService

    # TODO: Read agent names from config/config.yaml
    # Sorry if you are reading this code, hardcoding for now to move fast
    # and test things out.
    agent_name = "feng_stocks_news_agent"
    agent_name_1 = "feng_news_fact_checker_agent"

    context.logger.debug("Loaded instructions for stocks_news agent")

    # TODO: Read these from config/config.yaml
    # Step 1: Create model adapter (Infrastructure)
    model_adapter = PydanticAIModelAdapter(
        context=context,
        model_type=ModelType.OLLAMA,
        # model_name="qwen3-coder:latest",
        # model_name="qwen3-next:latest",
        # model_name="glm-4.7-flash:q8_0",
        # model_name="nemotron-3-nano:30b",
        # model_name="mistral",
        model_name="qwen3:30b",
        provider_config={
            "base_url": "http://localhost:11434/v1",
        },
    )

    # Step 2: Create agent dependencies with runtime context
    agent_deps = AgentDeps(
        agent_name=agent_name,
        search_lookback_hours=1,  # Only last hour of news
        target_regions=["US", "Asia", "Europe"],
        max_news_items=30,
        model_guidance="""# Model Accuracy Guidelines
- Use EXACT headlines from search results (verbatim, no paraphrasing)
- Use EXACT URLs from search results (copy character-for-character)
- Use page_age from search results for published_at timestamps
- Process ALL news items from search results, not just one
- Extract stock ticker if mentioned, otherwise use relevant index (SPX, NDX, etc.)
- Determine sentiment based on actual description content""",
    )

    # Step 3: Create agent provider (Infrastructure)
    agent_provider = PydanticAIAgentAdapter[str, NewsAnalysisReport](
        context=context,
        model_adapter=model_adapter,
        instructions_reader=InstructionsFileReader(context=context),
        output_type=NewsAnalysisReport,
        agent_name=agent_name,
        news_client=BraveSearchClient(
            api_key=context.secrets_provider.get_secret("BRAVE_API_KEY"),
        ),
        deps=agent_deps,
    )

    # Step 4: Create application service with injected dependencies
    stocks_news_service = StocksNewsService(
        ai_provider=agent_provider,
        context=context,
    )

    # async with BraveSearchClient(
    #     api_key=context.secrets_provider.get_secret("BRAVE_API_KEY"),
    # ) as search_client:
    #     response = await search_client.search("Latest stock market news", num_results=5)
    #     context.logger.info("Brave Search Response: %s", response.model_dump_json())
    # exit(0)
    # =========================================================================
    # APPLICATION EXECUTION
    # =========================================================================

    # Fetch and summarize stock market news from the last hour
    response = await stocks_news_service.get_news(
        # "First, read the latest new from outputs/20260124TXXXXXX_news.md "
        "Look up the latest stock market news from the last hour on the web. "
        "Summarize the key stock market news items from the last hour. "
        # "Don't search the web. "
        # "use brave_web_search tool to get more details about any news items you find relevant. "
        # "Use brave_news_search tool to get news articles. "
        # "use the parameter country and try other countries than US. "
        "Asia and Europe markets are equally important. "
        # "don't use brave_image_search tool and brave_video_search tool. "
        # "save the summary to the disk inside the outputs folder and explain where you saved it."
        # "Each news item in the summary should include the stock ticker, company name, and sentiment. "
        # "Each news item should have one or more sources cited. "
        # "Then Search the web for stock market news from the last hour. "
        # "Find significant news about major companies, earnings reports, "
        # "market movements, and breaking financial news. "
        # "Summarize each item with the stock ticker, company name, and sentiment. "
        # "Provide a concise summary of the overall market sentiment based on the news found. "
        # "Cite sources where applicable. "
        # "Lastly save the response in markdown format in the folder ./outputs/"
    )
    context.logger.info("Stock News Response:\n%s", response)

    context.logger.info("Agent Feng executed successfully")

    return 0


def main() -> None:
    """Synchronous entry point wrapper.

    This function serves as the main entry point called by the console script.
    It creates the application context, wraps the async_main function,
    and handles the event loop.

    Example:
        Called via console script::

            agent-feng
    """
    # Create application context (composition root responsibility)
    context = create_application_context(raise_on_missing_env=False)

    exit_code = asyncio.run(async_main(context))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
