from typing import Any

from pydantic import BaseModel

from app.agent.tool_result import ToolResult


class Observation(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result: ToolResult
