from app.agent.observation import Observation
from app.agent.plan import Plan, PlanStep
from app.agent.tool_registry import ToolRegistry
from app.agent.tool_result import ToolResult

FINAL_ANSWER_TOOL_NAME = "final_answer"


class PlanExecutor:
    """
    Executes a Plan by running each step's tool call through the existing
    ToolRegistry - the same tool-execution engine the Agent uses for its
    own tool calls.

    PlanExecutor ONLY executes what the Plan already specifies. It never
    calls an LLM, never decides what a step's tool_name or arguments
    should be, and never produces the user-facing final answer. A step
    left with empty arguments (because the Planner could not know them
    in advance) is executed exactly as-is; filling it in from a prior
    step's result is Runtime Variable Injection's job, not this class.

    A step failing - either ToolResult.success is False, or the step
    cannot be dispatched at all (unknown tool_name, mismatched
    arguments) - does not stop the plan. Every remaining step still
    runs, so the caller ends up with as complete a picture as possible
    instead of losing later, unrelated steps to one bad step.
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    async def execute(self, plan: Plan) -> list[Observation]:
        observations: list[Observation] = []

        for step in plan.steps:
            if step.tool_name == FINAL_ANSWER_TOOL_NAME:
                break

            result = await self._run_step(step)

            observations.append(
                Observation(
                    tool_name=step.tool_name,
                    arguments=step.arguments,
                    result=result,
                )
            )

            step.completed = True

        return observations

    async def _run_step(self, step: PlanStep) -> ToolResult:
        try:
            return await self._registry.execute(step.tool_name, step.arguments)
        except Exception as e:
            # A hallucinated tool_name, mismatched arguments, or any
            # other dispatch failure must not crash the whole plan - it
            # becomes a failed observation instead, same as every other
            # tool failure in this system.
            return ToolResult(
                success=False,
                content=f"Failed to execute step '{step.description}': {e}",
                metadata={"tool_name": step.tool_name},
            )
