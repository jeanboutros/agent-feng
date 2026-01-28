from datetime import datetime, timezone
from enum import StrEnum
import json
from typing import Any

from fastmcp import settings
from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    AgentStreamEvent,
    ModelSettings,
    PartDeltaEvent,
    RunContext,
)
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models import Model
from pydantic_ai.providers import Provider

from agent_feng.core import ApplicationContext
from agent_feng.core.abc import (
    AgentProvider,
    AIModelAdapter,
    InstructionsReader,
    WebSearcher,
)
from agent_feng.domain.models import AgentDeps


# TODO move to exceptions module
class ModelTypeError(Exception):
    """Custom exception for unsupported model types."""

    pass


# TODO move to abc module
class ModelType(StrEnum):
    OLLAMA = "ollama"


class PydanticAIModelAdapter(AIModelAdapter[Model]):
    """Adapter for integrating pydantic-ai Agent with the application."""

    def _load_model_type(
        self, model_type: ModelType
    ) -> tuple[type[Model], type[Provider[Any]]]:
        match model_type:
            case ModelType.OLLAMA:
                from pydantic_ai.models.openai import OpenAIChatModel as model
                from pydantic_ai.providers.ollama import OllamaProvider as provider

                return model, provider
            case _:
                raise ValueError(f"Unsupported model type: {model_type}")

    def __init__(
        self,
        context: ApplicationContext,
        model_name: str,
        model_type: ModelType,
        provider_config: dict[str, Any] | None = None,
        # instructions: str | None = None,
    ) -> None:
        model_cls, provider_cls = self._load_model_type(model_type)

        provider_config = provider_config or {}

        if "base_url" not in provider_config:
            raise ValueError(
                "provider_config must include 'base_url' for the provider."
            )

        # Configure Ollama-specific options via extra_body:
        # - num_ctx: Increase context window from default 4096 to 32768
        model_settings = ModelSettings(
            extra_body={
                "options": {
                    "num_ctx": 32768,  # Increase context window for Ollama
                }
            }
        )

        model = model_cls(
            model_name=model_name,
            provider=provider_cls(base_url=provider_config["base_url"]),
            settings=model_settings,
        )

        # self._agent = Agent(model=model, instructions=instructions or "")
        self._context = context
        self._logger = context.logger.getChild("PydanticAIAdapter")
        self._model = model

    @property
    def model(self) -> Model:
        """Get the underlying pydantic-ai model."""
        return self._model


class PydanticAIAgentAdapter[
    T,
    R,
](AgentProvider[Agent, T, R]):
    """Adapter for integrating pydantic-ai Agent with the application."""

    def __init__(
        self,
        context: ApplicationContext,
        model_adapter: PydanticAIModelAdapter,
        instructions_reader: InstructionsReader,
        agent_name: str,
        news_client: WebSearcher,
        output_type: type[R] = str,
        deps: AgentDeps | None = None,
    ) -> None:
        self._context = context
        self._model_adapter = model_adapter
        self._instructions = instructions_reader.read_instructions(
            agent_name=agent_name
        )
        self._logger = context.logger.getChild("PydanticAIAgentAdapter")
        self._agent_name = agent_name
        self._news_client = news_client
        self._deps = deps or AgentDeps(agent_name=agent_name)

        file_server = MCPServerStdio(
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                self._context.project_root.resolve().as_posix(),
            ],
        )

        accuweather_api_key = context.secrets_provider.get_secret("ACCUWEATHER_API_KEY")

        accu_weather = MCPServerStdio(
            command="npx",
            args=["-y", "@timlukahorstmann/mcp-weather"],
            env={"ACCUWEATHER_API_KEY": accuweather_api_key},
            max_retries=3,
        )

        brave_search_api_key = context.secrets_provider.get_secret("BRAVE_API_KEY")

        brave_search = MCPServerStdio(
            command="npx",
            args=["-y", "@brave/brave-search-mcp-server", "--transport", "stdio"],
            env={"BRAVE_API_KEY": brave_search_api_key},
            max_retries=3,
        )

        # Note: MCP filesystem tools (file_server) are DISABLED for stocks news agent
        # because the qwen3:30b model confuses search_files (filesystem) with search_news (web).
        # Re-enable only if the model is switched to one that handles tool disambiguation better.
        self._agent: Agent[AgentDeps, R] = Agent(
            model=model_adapter.model,
            system_prompt=self._instructions,
            output_type=output_type,
            deps_type=AgentDeps,
            toolsets=[
                # file_server,  # Disabled - causes tool confusion with search_news
                accu_weather,
                # brave_search,  # Using Python tool for news search instead
            ],
            retries=3,  # Allow more retries for output validation
        )

        # @self._agent.system_prompt
        # async def thinking_mode_prompt(ctx: RunContext[AgentDeps]) -> str:
        #     # /no_think disables qwen3's extended thinking mode to reduce verbosity
        #     return "/no_think"

        @self._agent.system_prompt
        async def environment_prompt(ctx: RunContext[AgentDeps]) -> str:
            deps = ctx.deps
            year = deps.current_datetime.year
            return f"""# Environment
Agent: {deps.agent_name}
Current datetime (UTC): {deps.current_datetime_iso}
Current year: {year} (THIS IS CORRECT - do NOT "fix" dates from {year})
Earliest news date: {deps.earliest_search_date_iso}
Search lookback: {deps.search_lookback_hours} hours
Target regions: {deps.regions_str}
Max news items: {deps.max_news_items}
Output format: {deps.output_format}

## CRITICAL: Include ALL news items
You MUST include EVERY news item returned by search_news in your final report.
Do NOT summarize multiple articles into one. Create a separate NewsItem for EACH result.
If search returns 30 results, your news_items array MUST have 30 entries.

{deps.model_guidance}"""

        @self._agent.system_prompt
        async def output_policy_prompt(ctx: RunContext[AgentDeps]) -> str:
            return """# Output Policy
- Return ONLY valid JSON. No markdown. No code blocks. No explanations.
- Match the required schema exactly with all required fields.
- Be concise. Do not add preamble or postamble.
- Include ALL news items from search results - do NOT aggregate or summarize into fewer items.
- Dates from search results are CORRECT. Do not modify or "fix" them.
- Copy URLs and headlines EXACTLY as returned by tools."""

        @self._agent.system_prompt
        async def tools_prompt(ctx: RunContext[AgentDeps]) -> str:
            return """# Tool Selection Guide

## CRITICAL: Choose the Right Tool for News
- For NEWS from the INTERNET -> call `search_news` (Brave Search API)
- For LOCAL FILES on disk -> call `search_files` or `read_file` (MCP Filesystem)

⚠️ NEVER use `search_files` to search for news. It only finds local files by filename.

## search_news (WEB SEARCH - USE THIS FOR FINANCIAL NEWS)
Searches the internet for news articles via Brave Search API.
- query (str): Search terms like "stock market news"  
- num_results (int): Number of results (default: 30)
Returns: title, url, description, page_age, meta_url from real web sources.

## get_current_iso_datetime
Returns current UTC datetime in ISO format. Use for retrieved_at timestamps.

## save_to_file (MANDATORY FINAL STEP)
Saves content to persistent storage. Call AFTER generating your report.
- content (str): The JSON string to save

## MCP Filesystem Tools (LOCAL FILES ONLY)
- search_files: Finds files by glob pattern (NOT web search)
- read_file: Reads local file by path
- list_directory: Lists folder contents
Only use if explicitly asked to access local files."""

        self.add_tool()

    @property
    def agent(self) -> Agent[AgentDeps, R]:
        """Get the underlying pydantic-ai agent."""
        return self._agent

    def add_tool(self) -> None:
        """Add a tool to the agent.

        Args:
            tool (Any): The tool to add.
        """

        @self._agent.tool
        async def get_agent_name(ctx: RunContext[AgentDeps]) -> Any:
            """Get the name of this agent."""
            return ctx.deps.agent_name

        @self._agent.tool
        async def get_current_iso_datetime(ctx: RunContext[AgentDeps]) -> Any:
            """Get the current UTC datetime in ISO format. Use this for timestamps."""
            return ctx.deps.current_datetime_iso

        @self._agent.tool
        async def get_agent_context(ctx: RunContext[AgentDeps]) -> dict[str, Any]:
            """Get full agent context including search boundaries and regions.

            Returns:
                dict with all agent configuration fields serialized to JSON-compatible format.
            """
            return ctx.deps.model_dump(mode="json")

        @self._agent.tool
        async def get_output_file_path(ctx: RunContext[AgentDeps]) -> Any:
            """Get the file path for saving output files."""
            ts = ctx.deps.current_datetime.strftime("%Y%m%dT%H%M%S")
            return f"outputs/{ts}Z_{ctx.deps.agent_name}.json"

        @self._agent.tool
        async def search_news(
            ctx: RunContext[AgentDeps], query: str, num_results: int | None = None
        ) -> Any:
            """Search the web for news articles. This is your PRIMARY tool for finding stock market news.

            Args:
                query: Search terms for finding news (e.g., 'stock market news Asia Europe')
                num_results: Number of results to return (default: 30)

            Returns:
                JSON with news results containing title, url, description, page_age, and meta_url fields.
            """
            actual_num_results = num_results or ctx.deps.max_news_items
            response = await self._news_client.search(
                query=query,
                num_results=actual_num_results,
            )
            return response.model_dump_json()

        @self._agent.tool
        async def save_to_file(ctx: RunContext[AgentDeps], content: str) -> str:
            """Save the news analysis report to a JSON file.

            Args:
                content: The JSON string containing the NewsAnalysisReport data.

            Returns:
                str: Confirmation message with the file path.
            """
            # Save the report to outputs folder
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")

            output_path = (
                self._context.project_root
                / "outputs"
                / f"{timestamp}Z_{self._agent_name}.json"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Parse and validate the JSON content
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                # If already a dict-like string representation, try to use as-is
                parsed_content = content

            with output_path.open("w", encoding="utf-8") as f:
                if isinstance(parsed_content, dict):
                    json.dump(parsed_content, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(parsed_content))

            self._logger.info("Saved report to %s", output_path)
            return f"Report saved successfully to {output_path}"

    async def _handle_event(self, event: AgentStreamEvent) -> None:
        """Handle intermediate events from the agent run.

        Args:
            event (Any): The event to handle.
        """
        if not isinstance(event, PartDeltaEvent):
            self._logger.debug("Intermediate event of type %s: %s", type(event), event)

    async def generate_response(self, input_data: T) -> R:
        """Generate a response from the AI agent.

        Args:
            input_data (str): The input string to process.

        Returns:
            str: The output generated by the agent.
        """

        # Configure Ollama-specific options via extra_body:
        # - num_ctx: Increase context window from default 4096 to 32768
        # - think: Disable qwen3's verbose thinking mode via API option
        model_settings = ModelSettings(
            extra_body={
                "options": {
                    "num_ctx": 32768,  # Increase context window for Ollama
                },
                "think": False,  # Disable qwen3 thinking mode
            }
        )

        user_prompt = str(input_data)

        response = ""
        async for event in self._agent.run_stream_events(
            user_prompt=user_prompt,
            deps=self._deps,
            model_settings=model_settings,
        ):
            if isinstance(event, AgentRunResultEvent):
                self._logger.debug("Final response received: %s", event.result)
                response = event.result.output
                return response
            else:
                await self._handle_event(event)


class PydanticAIAgentAdapter2[T, R](AgentProvider[Agent, T, R]):
    """Adapter for integrating pydantic-ai Agent with the application."""

    def __init__(
        self,
        context: ApplicationContext,
        model_adapter: PydanticAIModelAdapter,
        instructions_reader: InstructionsReader,
        agent_name: str,
        news_client: WebSearcher,
        output_type: type[R] = str,
        deps: AgentDeps | None = None,
    ) -> None:
        self._context = context
        self._model_adapter = model_adapter
        self._instructions = instructions_reader.read_instructions(
            agent_name=agent_name
        )
        self._logger = context.logger.getChild("PydanticAIAgentAdapter")
        self._agent_name = agent_name
        self._news_client = news_client
        self._deps = deps or AgentDeps(agent_name=agent_name)

        self._agent: Agent[AgentDeps, R] = Agent(
            model=model_adapter.model,
            system_prompt=self._instructions,
            output_type=output_type,
            deps_type=AgentDeps,
            toolsets=[],
            retries=3,  # Allow more retries for output validation
        )

        @self._agent.system_prompt
        async def environment_prompt(ctx: RunContext[AgentDeps]) -> str:
            deps = ctx.deps
            year = deps.current_datetime.year
            return f"""# Environment
Agent: {deps.agent_name}
Current datetime (UTC): {deps.current_datetime_iso}
Current year: {year} (THIS IS CORRECT - do NOT "fix" dates from {year})
Earliest news date: {deps.earliest_search_date_iso}
Search lookback: {deps.search_lookback_hours} hours
Target regions: {deps.regions_str}
Max news items: {deps.max_news_items}
Output format: {deps.output_format}

## CRITICAL: Include ALL news items
You MUST include EVERY news item returned by search_news in your final report.
Do NOT summarize multiple articles into one. Create a separate NewsItem for EACH result.
If search returns 30 results, your news_items array MUST have 30 entries.

{deps.model_guidance}"""

        @self._agent.system_prompt
        async def output_policy_prompt(ctx: RunContext[AgentDeps]) -> str:
            return """# Output Policy
- Return ONLY valid JSON. No markdown. No code blocks. No explanations.
- Match the required schema exactly with all required fields.
- Be concise. Do not add preamble or postamble.
- Include ALL news items from search results - do NOT aggregate or summarize into fewer items.
- Dates from search results are CORRECT. Do not modify or "fix" them.
- Copy URLs and headlines EXACTLY as returned by tools."""

        @self._agent.system_prompt
        async def tools_prompt(ctx: RunContext[AgentDeps]) -> str:
            return """# Tool Selection Guide

## CRITICAL: Choose the Right Tool for News
- For NEWS from the INTERNET -> call `search_news` (Brave Search API)

## search_news (WEB SEARCH - USE THIS FOR FINANCIAL NEWS)
Searches the internet for news articles via Brave Search API.
- query (str): Search terms like "stock market news"  
- num_results (int): Number of results (default: 30)
Returns: title, url, description, page_age, meta_url from real web sources.
"""

        self.add_tool()

    @property
    def agent(self) -> Agent[AgentDeps, R]:
        """Get the underlying pydantic-ai agent."""
        return self._agent

    def add_tool(self) -> None:
        """Add a tool to the agent."""

        @self._agent.tool
        async def search_news(
            ctx: RunContext[AgentDeps], query: str, num_results: int | None = None
        ) -> Any:
            """Search the web for news articles. This is your PRIMARY tool for finding stock market news.

            Args:
                query: Search terms for finding news (e.g., 'stock market news Asia Europe')
                num_results: Number of results to return (default: 30)

            Returns:
                JSON with news results containing title, url, description, page_age, and meta_url fields.
            """
            actual_num_results = num_results or ctx.deps.max_news_items
            response = await self._news_client.search(
                query=query,
                num_results=actual_num_results,
            )
            return response.model_dump_json()

    async def _handle_event(self, event: AgentStreamEvent) -> None:
        """Handle intermediate events from the agent run.

        Args:
            event (Any): The event to handle.
        """
        if not isinstance(event, PartDeltaEvent):
            self._logger.debug("Intermediate event of type %s: %s", type(event), event)

    async def generate_response(self, input_data: T) -> R:
        """Generate a response from the AI agent.

        Args:
            input_data (str): The input string to process.

        Returns:
            str: The output generated by the agent.
        """

        user_prompt = str(input_data)

        response = ""
        async for event in self._agent.run_stream_events(
            user_prompt=user_prompt,
            deps=self._deps,
        ):
            if isinstance(event, AgentRunResultEvent):
                self._logger.debug("Final response received: %s", event.result)
                response = event.result.output
                return response
            else:
                await self._handle_event(event)
