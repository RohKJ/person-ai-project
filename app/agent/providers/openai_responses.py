from __future__ import annotations

import json
from datetime import date
from typing import Any

from app.agent.errors import AgentExecutionError
from app.agent.registry import ToolRegistry


class OpenAIResponsesProvider:
    name = "openai"

    def __init__(
        self,
        registry: ToolRegistry,
        model: str,
        client: Any,
        today: date | None = None,
    ) -> None:
        self.registry = registry
        self.model = model
        self.client = client
        self.today = today or date.today()

    def run(self, query: str) -> dict[str, Any]:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=self._instructions(),
                input=query,
                tools=self.registry.openai_responses_tool_schemas(),
                tool_choice="required",
                parallel_tool_calls=False,
            )
        except Exception as exc:
            raise AgentExecutionError(f"OpenAI Responses API request failed: {exc}") from exc

        function_calls = [
            item for item in response.output if getattr(item, "type", None) == "function_call"
        ]
        if len(function_calls) != 1:
            raise AgentExecutionError(
                f"Expected exactly one function call, received {len(function_calls)}."
            )

        function_call = function_calls[0]
        try:
            tool_args = json.loads(function_call.arguments)
            tool = self.registry.get(function_call.name)
            result = self.registry.run(tool.name, tool_args)
        except Exception as exc:
            raise AgentExecutionError(f"OpenAI-selected tool execution failed: {exc}") from exc

        return {
            "query": query,
            "mode": self.name,
            "provider": self.name,
            "model": self.model,
            "answer": self.registry.format_answer(tool.name, result),
            "tool_name": tool.name,
            "tool_description": tool.description,
            "tool_args": tool.validate_args(tool_args),
            "route_reason": f"OpenAI Responses API selected {tool.name}",
            "result": result,
            "planner_metadata": {
                "response_id": getattr(response, "id", None),
                "function_call_id": getattr(function_call, "call_id", None),
            },
        }

    def _instructions(self) -> str:
        return (
            "You are a D2C brand operations tool router. "
            f"Today's date is {self.today.isoformat()}. "
            "Call exactly one function tool that best answers the user's question. "
            "Resolve Korean relative date expressions such as 오늘, 어제, 이번 주 into YYYY-MM-DD values. "
            "When no date range is specified, use the latest 7-day period ending today. "
            "When inventory risk days are not specified, use 7. "
            "When an anomaly threshold is not specified, use 40 percent. "
            "When a report type is not specified, use daily. "
            "Never answer with invented metrics or numeric claims. "
            "The application will execute the selected tool and format the grounded answer."
        )
