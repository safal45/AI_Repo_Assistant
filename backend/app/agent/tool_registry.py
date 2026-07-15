import inspect
from typing import Any

from app.agent.tool import Tool
from app.agent.tool_result import ToolResult


class ToolRegistry:

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")

        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> Tool:
        tool = self._tools.get(tool_name)

        if tool is None:
            raise ValueError(f"Tool '{tool_name}' is not registered.")

        return tool
    
    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())
    
    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ):
        tool = self.get(tool_name)

        try:
            result = tool.function(**arguments)

            if inspect.isawaitable(result):
                result = await result

            return result
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Tool '{tool_name}' failed: {e}",
            )