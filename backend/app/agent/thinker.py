import json

from pydantic import ValidationError

from app.agent.action import AgentAction
from app.agent.observation import Observation
from app.agent.prompt_builder import AgentPromptBuilder
from app.agent.tool_registry import ToolRegistry
from app.ai.llm.factory import get_llm


class InvalidAgentActionError(Exception):
    """Raised when the LLM response cannot be parsed into a valid AgentAction."""


def _extract_json(response: str) -> str:
    text = response.strip()

    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()

    return text


class AgentThinker:
    """
    Decides exactly one next AgentAction per call, given only the current
    observations - it does not plan ahead. Imperative multi-step queries
    (e.g. "search, then read the file") can still cause the underlying LLM
    to narrate multiple steps instead of one action; see Agent's docstring.
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry
        self._prompt_builder = AgentPromptBuilder()

    async def think(
        self,
        user_query: str,
        observations: list[Observation],
    ) -> AgentAction:
        tools = self._registry.list_tools()

        prompt = self._prompt_builder.build(
            user_query=user_query,
            tools=tools,
            observations=observations,
        )

        llm = get_llm()

        response = await llm.generate(
            prompt=prompt,
            system_prompt=self._prompt_builder.build_system_prompt(),
            json_mode=True,
        )

        try:
            data = json.loads(_extract_json(response))
            return AgentAction.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise InvalidAgentActionError(
                f"LLM returned an invalid agent action: {response!r}"
            ) from e
