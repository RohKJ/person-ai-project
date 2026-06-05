from __future__ import annotations

from typing import Any

from app.agent.tools import AGENT_TOOLS, AgentTool


class ToolRegistry:
    def __init__(self, tools: tuple[AgentTool, ...] = AGENT_TOOLS) -> None:
        self._tools = tools
        self._by_name = {tool.name: tool for tool in tools}
        defaults = [tool for tool in tools if tool.default]
        if len(defaults) != 1:
            raise ValueError("ToolRegistry requires exactly one default tool.")
        self._default_tool = defaults[0]

    def get(self, tool_name: str) -> AgentTool:
        try:
            return self._by_name[tool_name]
        except KeyError as exc:
            raise ValueError(f"Unknown agent tool: {tool_name}") from exc

    def select_tool_name(self, normalized_query: str) -> str:
        for tool in self._tools:
            if any(keyword in normalized_query for keyword in tool.keywords):
                return tool.name
        return self._default_tool.name

    def run(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        return self.get(tool_name).run(args)

    def format_answer(self, tool_name: str, result: dict[str, Any]) -> str:
        return self.get(tool_name).format_answer(result)

    def describe(self, tool_name: str) -> dict[str, Any]:
        tool = self.get(tool_name)
        return {
            "name": tool.name,
            "description": tool.description,
            "args_schema": tool.args_model.model_json_schema(),
            "keywords": list(tool.keywords),
            "default": tool.default,
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return [self.describe(tool.name) for tool in self._tools]

    def openai_tool_schemas(self) -> list[dict[str, Any]]:
        return [tool.openai_tool_schema() for tool in self._tools]


DEFAULT_TOOL_REGISTRY = ToolRegistry()
