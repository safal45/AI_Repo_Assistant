from pydantic import BaseModel, Field

from app.agent.tool_result import ToolResult


class ExecutionContext(BaseModel):
    tool_results: list[ToolResult] = Field(default_factory=list)