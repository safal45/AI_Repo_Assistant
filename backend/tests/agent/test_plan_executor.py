import unittest

from app.agent.plan import Plan, PlanStep
from app.agent.plan_executor import PlanExecutor
from app.agent.tool import Tool
from app.agent.tool_registry import ToolRegistry
from app.agent.tool_result import ToolResult


def _echo_tool(**kwargs) -> ToolResult:
    return ToolResult(
        success=True,
        content=f"echoed: {kwargs}",
        metadata={"received": kwargs},
    )


def _failing_result_tool(**kwargs) -> ToolResult:
    return ToolResult(success=False, content="simulated failure", metadata={})


def _crashing_tool(**kwargs):
    raise RuntimeError("boom")


def _build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        Tool(name="echo_tool", description="Echoes its arguments.", function=_echo_tool)
    )
    registry.register(
        Tool(
            name="failing_result_tool",
            description="Always returns a failed ToolResult.",
            function=_failing_result_tool,
        )
    )
    registry.register(
        Tool(name="crashing_tool", description="Always raises.", function=_crashing_tool)
    )
    return registry


class PlanExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_executes_steps_in_order_and_marks_them_completed(self):
        plan = Plan(
            steps=[
                PlanStep(description="First", tool_name="echo_tool", arguments={"query": "a"}),
                PlanStep(description="Second", tool_name="echo_tool", arguments={"query": "b"}),
            ]
        )

        executor = PlanExecutor(_build_registry())
        observations = await executor.execute(plan)

        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0].arguments, {"query": "a"})
        self.assertEqual(observations[1].arguments, {"query": "b"})
        self.assertTrue(plan.steps[0].completed)
        self.assertTrue(plan.steps[1].completed)

    async def test_stops_before_executing_final_answer_step(self):
        plan = Plan(
            steps=[
                PlanStep(description="Gather", tool_name="echo_tool", arguments={"query": "a"}),
                PlanStep(description="Answer", tool_name="final_answer", arguments={}),
            ]
        )

        executor = PlanExecutor(_build_registry())
        observations = await executor.execute(plan)

        self.assertEqual(len(observations), 1)
        self.assertTrue(plan.steps[0].completed)
        self.assertFalse(plan.steps[1].completed)

    async def test_continues_after_a_failed_tool_result(self):
        plan = Plan(
            steps=[
                PlanStep(description="Fails", tool_name="failing_result_tool", arguments={}),
                PlanStep(description="Still runs", tool_name="echo_tool", arguments={"query": "b"}),
            ]
        )

        executor = PlanExecutor(_build_registry())
        observations = await executor.execute(plan)

        self.assertEqual(len(observations), 2)
        self.assertFalse(observations[0].result.success)
        self.assertTrue(observations[1].result.success)
        self.assertTrue(plan.steps[0].completed)
        self.assertTrue(plan.steps[1].completed)

    async def test_unregistered_tool_name_produces_failed_observation_not_a_crash(self):
        plan = Plan(
            steps=[PlanStep(description="Bad tool", tool_name="does_not_exist", arguments={})]
        )

        executor = PlanExecutor(_build_registry())
        observations = await executor.execute(plan)

        self.assertEqual(len(observations), 1)
        self.assertFalse(observations[0].result.success)
        self.assertTrue(plan.steps[0].completed)

    async def test_tool_that_raises_produces_failed_observation_not_a_crash(self):
        plan = Plan(
            steps=[PlanStep(description="Crashes", tool_name="crashing_tool", arguments={})]
        )

        executor = PlanExecutor(_build_registry())
        observations = await executor.execute(plan)

        self.assertEqual(len(observations), 1)
        self.assertFalse(observations[0].result.success)
        self.assertIn("boom", observations[0].result.content)

    async def test_empty_plan_returns_no_observations(self):
        plan = Plan(steps=[])

        executor = PlanExecutor(_build_registry())
        observations = await executor.execute(plan)

        self.assertEqual(observations, [])

    async def test_arguments_are_passed_through_unmodified(self):
        # PlanExecutor must NOT attempt to fill in / guess empty
        # arguments - that is Runtime Variable Injection's job, not
        # built yet. An empty-arguments step is executed exactly as-is.
        plan = Plan(
            steps=[PlanStep(description="No args yet", tool_name="echo_tool", arguments={})]
        )

        executor = PlanExecutor(_build_registry())
        observations = await executor.execute(plan)

        self.assertEqual(observations[0].result.metadata["received"], {})


if __name__ == "__main__":
    unittest.main()
