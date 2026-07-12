from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
