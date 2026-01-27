from datetime import datetime, timezone
from enum import StrEnum
import json
from typing import Any

from pydantic_ai import (
    Agent,
    AgentRunResultEvent,
    AgentStreamEvent,
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
from agent_feng.domain.models import NewsAnalysisReport


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

        model = model_cls(
            model_name=model_name,
            provider=provider_cls(base_url=provider_config["base_url"]),
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
    ) -> None:
        self._context = context
        self._model_adapter = model_adapter
        self._instructions = instructions_reader.read_instructions(
            agent_name=agent_name
        )
        self._logger = context.logger.getChild("PydanticAIAgentAdapter")
        self._agent_name = agent_name
        self._news_client = news_client

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

        self._agent = Agent(
            model=model_adapter.model,
            system_prompt=self._instructions,
            output_type=output_type,
            toolsets=[
                file_server,
                accu_weather,
                # brave_search,
            ],
            retries=3,  # Allow more retries for output validation
        )

        @self._agent.system_prompt
        async def agent_name_prompt(ctx: RunContext) -> str:
            return f"You are an AI agent named {self._agent_name}."

        @self._agent.system_prompt
        async def current_datetime_prompt(ctx: RunContext) -> str:
            current_datetime = datetime.now(tz=timezone.utc).isoformat(
                sep=" ", timespec="seconds"
            )
            return f"The current date and time is {current_datetime}."

        @self._agent.system_prompt
        async def json_output_prompt(ctx: RunContext) -> str:
            return (
                "CRITICAL: Your final response MUST be valid JSON only. "
                "Do NOT include markdown, explanations, or any text outside the JSON object. "
                "Do NOT wrap JSON in code blocks. "
                "The JSON must match the required schema exactly with all required fields."
            )

        self.add_tool()

    @property
    def agent(self) -> Agent:
        """Get the underlying pydantic-ai agent."""
        return self._agent

    def add_tool(self) -> None:
        """Add a tool to the agent.

        Args:
            tool (Any): The tool to add.
        """

        @self._agent.tool
        async def get_agent_name(ctx: RunContext) -> Any:
            return self._agent_name

        @self._agent.tool
        async def get_current_iso_datetime(ctx: RunContext) -> Any:
            return datetime.now(tz=timezone.utc).isoformat(sep="T", timespec="seconds")

        @self._agent.tool
        async def get_output_file_path(ctx: RunContext) -> Any:
            ts = datetime.now(tz=timezone.utc).isoformat(sep="T", timespec="seconds")
            return f"outputs/{ts}Z_{self._agent_name}.md"

        @self._agent.tool
        async def search_news(
            ctx: RunContext, query: str, num_results: int = 30
        ) -> Any:
            response = await self._news_client.search(
                query=query,
                num_results=num_results,
            )
            return response.model_dump_json()

        @self._agent.tool
        async def save_to_file(ctx: RunContext, content: str) -> str:
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

        response = ""
        i = 0
        async for event in self._agent.run_stream_events(
            user_prompt=input_data,
        ):
            if isinstance(event, AgentRunResultEvent):
                self._logger.debug("Final response received: %s", event.result)
                response = event.result.output
                return response
            else:
                await self._handle_event(event)
