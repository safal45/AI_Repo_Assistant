import json
import unittest
from unittest.mock import AsyncMock, patch

from app.agent.plan import Plan
from app.agent.planner import EmptyPlanError, InvalidPlanError, Planner
from app.agent.tool import Tool
from app.agent.tool_registry import ToolRegistry


def _registry_with_dummy_tools() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="search_repository",
            description="Search the indexed repository for relevant code.",
            function=lambda **_: None,
        )
    )
    registry.register(
        Tool(
            name="read_file",
            description="Read the full contents of one file.",
            function=lambda **_: None,
        )
    )
    return registry


class PlannerTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.agent.planner.get_llm")
    async def test_returns_valid_plan(self, mock_get_llm):
        raw_plan = {
            "steps": [
                {
                    "description": "Search for JWT authentication implementation",
                    "tool_name": "search_repository",
                    "arguments": {"query": "JWT authentication"},
                },
                {
                    "description": "Summarize the implementation",
                    "tool_name": "final_answer",
                    "arguments": {},
                },
            ]
        }
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = json.dumps(raw_plan)
        mock_get_llm.return_value = mock_llm

        planner = Planner(_registry_with_dummy_tools())
        plan = await planner.create_plan("Explain how JWT authentication works.")

        self.assertIsInstance(plan, Plan)
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].tool_name, "search_repository")
        self.assertEqual(plan.steps[0].arguments, {"query": "JWT authentication"})
        self.assertFalse(plan.steps[0].completed)
        self.assertEqual(plan.steps[1].tool_name, "final_answer")

        mock_llm.generate.assert_awaited_once()
        _, kwargs = mock_llm.generate.call_args
        self.assertTrue(kwargs["json_mode"])

    @patch("app.agent.planner.get_llm")
    async def test_invalid_json_raises_clean_exception(self, mock_get_llm):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = "this is not json at all"
        mock_get_llm.return_value = mock_llm

        planner = Planner(_registry_with_dummy_tools())

        with self.assertRaises(InvalidPlanError):
            await planner.create_plan("Explain how JWT authentication works.")

    @patch("app.agent.planner.get_llm")
    async def test_malformed_step_raises_clean_exception(self, mock_get_llm):
        # Missing required "tool_name" on a step should fail Pydantic
        # validation and surface as InvalidPlanError, not a raw
        # ValidationError leaking out of Planner.
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = json.dumps(
            {"steps": [{"description": "Do something"}]}
        )
        mock_get_llm.return_value = mock_llm

        planner = Planner(_registry_with_dummy_tools())

        with self.assertRaises(InvalidPlanError):
            await planner.create_plan("Explain how JWT authentication works.")

    @patch("app.agent.planner.get_llm")
    async def test_empty_plan_is_rejected(self, mock_get_llm):
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = json.dumps({"steps": []})
        mock_get_llm.return_value = mock_llm

        planner = Planner(_registry_with_dummy_tools())

        with self.assertRaises(EmptyPlanError):
            await planner.create_plan("Explain how JWT authentication works.")


if __name__ == "__main__":
    unittest.main()
