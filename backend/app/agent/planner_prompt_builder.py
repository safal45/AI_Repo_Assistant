import json

from app.agent.tool import Tool


PLANNER_SYSTEM_PROMPT = """
You are a planning system for a repository-aware coding assistant.

Your only job is to break a user's request into an ordered list of
logical, executable steps. You do NOT execute anything yourself, and you
do NOT know the result of any step until that step actually runs later.

Each step must specify:
- description: a short human-readable explanation of what the step does.
- tool_name: the name of one of the available tools this step will use,
  or "final_answer" for the last step that summarizes the findings for
  the user.
- arguments: the arguments to call that tool with, as a JSON object.

Rules:
- Do NOT invent file paths, function names, or any other repository
  detail you cannot already be certain of. You have not searched the
  repository yet - a search or grep step must come before any step that
  needs a real path.
- If a step's arguments depend on the result of an earlier step (for
  example, a file path that a search step will discover), leave
  "arguments" as an empty object {}. Do not guess a placeholder value.
- Keep the plan as short as possible while still fully answering the
  request.
- Return ONLY a single valid JSON object - no markdown fences, no
  commentary before or after it.
"""


class PlannerPromptBuilder:
    """
    Builds the prompt sent to the LLM when asking it to produce a Plan.

    Deliberately independent from AgentPromptBuilder: the Planner and the
    Agent ask the LLM two different questions ("what is the whole shape
    of this task?" vs "what is the single next action, given what has
    actually happened so far?"). Mixing their prompts would couple two
    concerns that need to evolve separately.
    """

    def build_system_prompt(self) -> str:
        return PLANNER_SYSTEM_PROMPT

    def build(self, user_query: str, tools: list[Tool]) -> str:
        prompt = "Available tools:\n\n"

        for tool in tools:
            prompt += f"- {tool.name}: {tool.description}\n"

        prompt += (
            '\n(You may also use "final_answer" as a tool_name for the '
            "final step, to mark where the findings should be summarized "
            "for the user.)\n"
        )

        prompt += f"\nUser Request:\n\n{user_query}\n"

        example = {
            "steps": [
                {
                    "description": "Search for JWT authentication implementation",
                    "tool_name": "search_repository",
                    "arguments": {"query": "JWT authentication"},
                },
                {
                    "description": "Read the most relevant authentication file",
                    "tool_name": "read_file",
                    "arguments": {},
                },
                {
                    "description": "Summarize the implementation",
                    "tool_name": "final_answer",
                    "arguments": {},
                },
            ]
        }

        prompt += f"""
Respond with ONLY a single JSON object, and nothing else before or after
it, in exactly this shape:

{json.dumps(example, indent=2)}

Each entry in "steps" must have "description", "tool_name", and
"arguments". Do not add any field that is not shown above.
"""

        return prompt
