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
from pathlib import Path
import sys

import aiofiles

from agent_feng.core import ApplicationContext, create_application_context
from agent_feng.domain.brave_search import BraveNewsSearchApiResponse
from agent_feng.domain.models import AgentDeps, NewsAnalysisReport

from agent_feng.infrastructure.config_loader import YamlConfigLoader
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
    logger = context.logger

    logger.info("Agent Feng starting up")
    logger.info("Environment: %s", context.environment.value)
    logger.info("Log level: %s", context.log_level.value)
    logger.info("Project root: %s", context.project_root)

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

    config_loader = YamlConfigLoader(config_path=context.config_path / "config.yaml")
    agents_config = await config_loader.get_property("agents")

    agent_configs = agents_config[0]

    logger.debug("Loaded agents configuration: %s", agent_configs)
    agent_name = agent_configs["name"]

    logger.info("Initializing agent: %s", agent_name)

    # TODO: add validation
    model_type = ModelType(agent_configs["model_type"].lower())
    model_name = agent_configs["model_name"]
    provider_config = agent_configs.get("provider_config", {})
    logger.debug("Model Type: %s, Model Name: %s", model_type, model_name)
    logger.debug("Provider Config: %s", provider_config)

    guidance_file_path = Path(agent_configs.get("guidance_file"))
    if guidance_file_path.exists():
        logger.info("Using guidance file: %s", guidance_file_path)
        async with aiofiles.open(guidance_file_path, mode="rt", encoding="utf-8") as f:
            model_guidance = await f.read()
            logger.debug("Model Guidance: %s", model_guidance)
    else:
        logger.warning(
            "Guidance file %s does not exist. Using default guidance.",
            guidance_file_path,
        )
        model_guidance = ""

    # TODO: Read these from config/config.yaml
    # Step 1: Create model adapter (Infrastructure)
    model_adapter = PydanticAIModelAdapter(
        context=context,
        model_type=model_type,
        model_name=model_name,
        provider_config=provider_config,
    )

    # Step 2: Create agent dependencies with runtime context
    agent_deps = AgentDeps(
        agent_name=agent_name,
        search_lookback_hours=1,  # Only last hour of news
        target_regions=["US", "Asia", "Europe"],
        max_news_items=30,
        model_guidance=model_guidance,
    )

    # Step 3: Create agent provider (Infrastructure)
    agent_provider = PydanticAIAgentAdapter[str, BraveNewsSearchApiResponse](
        context=context,
        model_adapter=model_adapter,
        instructions_reader=InstructionsFileReader(context=context),
        output_type=BraveNewsSearchApiResponse,
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
