from typing import Any

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """
    One unit of work inside a Plan.

    A PlanStep is pure data - it does not execute anything itself. A
    future PlanExecutor is what will hand each step to the existing
    Agent/ToolRegistry to actually run.
    """

    description: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False


class Plan(BaseModel):
    """
    An ordered sequence of PlanSteps produced by the Planner for a single
    user query. Plan has no behavior of its own.
    """

    steps: list[PlanStep] = Field(default_factory=list)
