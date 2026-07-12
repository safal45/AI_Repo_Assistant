import unittest

from app.agent.planner_prompt_builder import PlannerPromptBuilder
from app.agent.tool import Tool


class PlannerPromptBuilderTests(unittest.TestCase):
    def setUp(self):
        self.builder = PlannerPromptBuilder()
        self.tools = [
            Tool(
                name="search_repository",
                description="Search the repo for relevant code.",
                function=lambda **_: None,
            ),
            Tool(
                name="read_file",
                description="Read a file by path.",
                function=lambda **_: None,
            ),
        ]

    def test_system_prompt_defines_planning_role(self):
        system_prompt = self.builder.build_system_prompt()

        self.assertIn("planning system", system_prompt.lower())
        self.assertIn("Return ONLY", system_prompt)

    def test_prompt_lists_available_tools(self):
        prompt = self.builder.build(user_query="Explain JWT auth.", tools=self.tools)

        self.assertIn("search_repository", prompt)
        self.assertIn("read_file", prompt)
        self.assertIn("Search the repo for relevant code.", prompt)

    def test_prompt_includes_user_query(self):
        prompt = self.builder.build(user_query="Explain JWT auth.", tools=self.tools)

        self.assertIn("Explain JWT auth.", prompt)

    def test_prompt_includes_json_example_shape(self):
        prompt = self.builder.build(user_query="Explain JWT auth.", tools=self.tools)

        self.assertIn('"steps"', prompt)
        self.assertIn('"description"', prompt)
        self.assertIn('"tool_name"', prompt)
        self.assertIn('"arguments"', prompt)
        self.assertIn('"final_answer"', prompt)


if __name__ == "__main__":
    unittest.main()
