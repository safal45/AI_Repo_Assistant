import json

from pydantic import ValidationError

from app.agent.plan import Plan
from app.agent.planner_prompt_builder import PlannerPromptBuilder
from app.agent.tool_registry import ToolRegistry
from app.ai.llm.factory import get_llm


class InvalidPlanError(Exception):
    """Raised when the LLM response cannot be parsed into a valid Plan."""


class EmptyPlanError(InvalidPlanError):
    """Raised when the parsed Plan contains zero steps."""


def _extract_json(response: str) -> str:
    text = response.strip()

    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()

    return text


class Planner:
    """
    Produces a Plan for a user query.

    Planner ONLY creates a Plan - it never calls
    ToolRegistry.execute(), never touches AgentState, and never calls
    Agent.run(). A future PlanExecutor is responsible for turning a Plan
    into real tool calls via the existing Agent.
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry
        self._prompt_builder = PlannerPromptBuilder()

    async def create_plan(self, user_query: str) -> Plan:
        tools = self._registry.list_tools()

        prompt = self._prompt_builder.build(user_query=user_query, tools=tools)

        llm = get_llm()

        response = await llm.generate(
            prompt=prompt,
            system_prompt=self._prompt_builder.build_system_prompt(),
            json_mode=True,
        )

        try:
            data = json.loads(_extract_json(response))
            plan = Plan.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise InvalidPlanError(
                f"LLM returned an invalid plan: {response!r}"
            ) from e

        if not plan.steps:
            raise EmptyPlanError(
                f"LLM returned a plan with zero steps: {response!r}"
            )

        return plan
