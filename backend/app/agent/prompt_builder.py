import json

from app.agent.observation import Observation
from app.agent.tool import Tool


SYSTEM_PROMPT = """
You are an expert software engineer acting as a repository-scoped coding
assistant.

Ground every final answer ONLY in the tool observations gathered during
this conversation - never answer from general background knowledge about
programming. If the observations gathered so far do not contain enough
information to answer the user's request, call another tool instead of
guessing.

When you give a final_answer:
- Be specific: cite exact file paths, function/class names, and line
numbers when they appear in the observations.
- Quote or paraphrase the actual retrieved code/content - do not describe
what such code "usually" looks like in general.
- If, after using the available tools, the observations still do not
contain the answer, respond with final_answer and say plainly that the
information could not be found in the repository. Never hallucinate.
"""


class AgentPromptBuilder:

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def build(
        self,
        user_query: str,
        tools: list[Tool],
        observations: list[Observation] | None = None,
    ) -> str:

        prompt = """
You are an AI agent that solves tasks step by step.

Available tools:

"""

        for tool in tools:
            prompt += (
                f"- {tool.name}: "
                f"{tool.description}\n"
            )

        prompt += f"""

User Request:

{user_query}
"""

        if observations:
            prompt += "\nPrevious Observations\n\n"

            for observation in observations:
                prompt += f"""Tool:
{observation.tool_name}

Arguments:
{json.dumps(observation.arguments, indent=2)}

Result:
{observation.result.content}

---------------------------------

"""

            prompt += """
The observations above were already retrieved. Do not call a tool again
with the same or a rephrased version of a query you already used. If the
observations contain information relevant to the user's request, you must
respond with "final_answer" now, grounding it strictly in those
observations as described in your instructions. If none of the
observations are relevant or sufficient, call a different tool rather
than repeating one that already failed.
"""
        else:
            prompt += """
No tools have been called yet. You must NOT respond with "final_answer"
until you have gathered real information about this repository - respond
with a "tool" action now.
"""

        prompt += """
Decide the single next action. You may only take ONE action per response.

You must NOT simulate, fabricate, or predict tool results yourself, and you
must NOT write out multiple steps, reasoning, explanations, or markdown
code fences. Only a real tool call, executed by the system, produces an
observation - never invent one.

Respond with ONLY a single JSON object, and nothing else before or after
it, in one of these two exact shapes:

To call a tool:
{"action_type": "tool", "tool_name": "<one of the tool names above>", "arguments": {...}}

To give the final answer (use this as soon as the observations already
gathered are enough to answer the user's request):
{"action_type": "final_answer", "answer": "<your final answer>"}

Example of a correct response (nothing else on the line, no other text):
{"action_type": "tool", "tool_name": "grep_code", "arguments": {"pattern": "JWT_SECRET"}}

Even if the user's request describes several steps (e.g. "grep for X, then
read the file"), you still respond with only ONE action now. The next step
will be decided later, after the real observation for this action comes
back.
"""

        return prompt