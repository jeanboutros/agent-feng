import datetime
from enum import StrEnum
import os
from typing import Any
from pydantic_ai import Agent, AgentRunResultEvent, AgentStreamEvent, RunContext
from pydantic_ai.models import Model
from pydantic_ai.providers import Provider
from pydantic_ai.mcp import MCPServerStdio
from agent_feng.core import ApplicationContext
from agent_feng.core.abc import AIModelAdapter, AgentProvider


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


class PydanticAIAgentAdapter[T, R](AgentProvider[Agent, T, R]):
    """Adapter for integrating pydantic-ai Agent with the application."""

    def __init__(
        self,
        context: ApplicationContext,
        model_adapter: PydanticAIModelAdapter,
        instructions: str,
        agent_name: str,
        output_type: type[R] = str,
    ) -> None:
        self._context = context
        self._model_adapter = model_adapter
        self._instructions = instructions
        self._logger = context.logger.getChild("PydanticAIAgentAdapter")
        self._agent_name = agent_name
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
        )

        brave_search_api_key = context.secrets_provider.get_secret("BRAVE_API_KEY")

        brave_search = MCPServerStdio(
            command="npx",
            args=["-y", "@brave/brave-search-mcp-server", "--transport", "stdio"],
            env={"BRAVE_API_KEY": brave_search_api_key},
        )

        self._agent = Agent(
            model=model_adapter.model,
            instructions=instructions,
            output_type=output_type,
            toolsets=[file_server, accu_weather, brave_search],
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
            return datetime.datetime.now(tz=datetime.timezone.utc).isoformat(
                sep="T", timespec="seconds"
            )

    async def _handle_event(self, event: AgentStreamEvent) -> None:
        """Handle intermediate events from the agent run.

        Args:
            event (Any): The event to handle.
        """
        self._logger.debug("Intermediate event: %s of type %s", event, type(event))

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
            user_prompt=input_data, instructions=self._instructions
        ):
            if isinstance(event, AgentRunResultEvent):
                self._logger.debug("Final response received: %s", event.result)
                response = event.result.output
                return response
            else:
                await self._handle_event(event)
