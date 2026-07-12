from app.agent.observation import Observation
from app.agent.state import AgentState
from app.agent.thinker import AgentThinker
from app.agent.tool_registry import ToolRegistry
from app.agent.tool_result import ToolResult


class AgentMaxIterationsError(Exception):
    """Raised when the agent does not reach a final answer within its iteration limit."""


class Agent:
    """
    Runs a Think -> One Action -> Observe loop until the thinker returns a
    final_answer or max_iterations is hit.

    Known limitation (expected, not a bug): a single-action thinker has no
    way to hold a multi-step plan across iterations, so a user query that
    itself narrates several steps ("grep for X, then read the file") can
    push the LLM to hallucinate the whole trace in one response instead of
    returning one action. This is inherent to the current architecture and
    is intended to be resolved by an upcoming planning layer, not by
    retries or prompt patches at this stage.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        thinker: AgentThinker,
        max_iterations: int = 8,
    ):
        self.registry = registry
        self.thinker = thinker
        self.max_iterations = max_iterations

    async def run(self, user_query: str) -> str:
        state = AgentState(user_query=user_query)

        for _ in range(self.max_iterations):
            action = await self.thinker.think(
                user_query=state.user_query,
                observations=state.observations,
            )

            if action.action_type == "final_answer":
                if not state.observations:
                    state.observations.append(
                        Observation(
                            tool_name="system_notice",
                            arguments={},
                            result=ToolResult(
                                success=False,
                                content=(
                                    "You attempted to give a final_answer "
                                    "without calling any tool first. You "
                                    "must call a tool to gather real "
                                    "information about this repository "
                                    "before answering."
                                ),
                            ),
                        )
                    )
                    continue

                state.completed = True
                return action.answer

            arguments = action.arguments or {}

            result = await self.registry.execute(
                action.tool_name,
                arguments,
            )

            state.observations.append(
                Observation(
                    tool_name=action.tool_name,
                    arguments=arguments,
                    result=result,
                )
            )

        raise AgentMaxIterationsError(
            f"Agent did not reach a final answer within "
            f"{self.max_iterations} iterations."
        )