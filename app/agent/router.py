from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.agent.registry import DEFAULT_TOOL_REGISTRY, ToolRegistry


@dataclass
class RouteDecision:
    tool_name: str
    tool_args: dict[str, Any]
    route_reason: str


class AgentRouter:
    """Rule-based mock agent router.

    The router chooses a registered analysis tool from natural language, validates
    tool arguments with Pydantic, then formats only values returned by that tool.
    This keeps numeric facts grounded in SQL-backed analysis functions and leaves
    a clean extension point for OpenAI Tool Calling or LangGraph.
    """

    def __init__(
        self,
        mode: str | None = None,
        today: date | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.mode = mode or os.getenv("AGENT_MODE", "mock")
        self.today = today or date.today()
        self.registry = registry or DEFAULT_TOOL_REGISTRY

    def route(self, query: str) -> RouteDecision:
        normalized = query.strip().lower()
        tool_name = self.registry.select_tool_name(normalized)
        tool = self.registry.get(tool_name)
        route_reason = (
            f"matched keywords: {', '.join(keyword for keyword in tool.keywords if keyword in normalized)}"
            if any(keyword in normalized for keyword in tool.keywords)
            else "defaulted to daily sales summary"
        )
        return RouteDecision(
            tool_name=tool_name,
            tool_args=self._build_tool_args(tool_name, normalized),
            route_reason=route_reason,
        )

    def run(self, query: str) -> dict[str, Any]:
        decision = self.route(query)
        tool = self.registry.get(decision.tool_name)
        result = self.registry.run(decision.tool_name, decision.tool_args)
        return {
            "query": query,
            "mode": self.mode,
            "answer": self.registry.format_answer(decision.tool_name, result),
            "tool_name": decision.tool_name,
            "tool_description": tool.description,
            "tool_args": decision.tool_args,
            "route_reason": decision.route_reason,
            "result": result,
        }

    def _extract_target_date(self, normalized_query: str) -> date:
        if "어제" in normalized_query:
            return self.today - timedelta(days=1)
        if "그제" in normalized_query:
            return self.today - timedelta(days=2)
        return self.today

    def _extract_period(self, normalized_query: str) -> tuple[date, date]:
        if "이번 주" in normalized_query or "이번주" in normalized_query:
            start = self.today - timedelta(days=self.today.weekday())
            return start, self.today
        if "어제" in normalized_query:
            target = self.today - timedelta(days=1)
            return target, target
        if "오늘" in normalized_query:
            return self.today, self.today
        return self.today - timedelta(days=6), self.today

    def _extract_days(self, normalized_query: str, default_days: int = 7) -> int:
        match = re.search(r"(\d{1,3})\s*일", normalized_query)
        if not match:
            return default_days
        return max(1, int(match.group(1)))

    def _build_tool_args(self, tool_name: str, normalized_query: str) -> dict[str, Any]:
        target_date = self._extract_target_date(normalized_query)
        start_date, end_date = self._extract_period(normalized_query)

        if tool_name == "generate_slack_report":
            return {
                "report_type": "daily",
                "date": target_date.isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        if tool_name == "get_campaign_performance":
            return {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
        if tool_name == "check_inventory_risk":
            return {"days": self._extract_days(normalized_query)}
        if tool_name == "summarize_reviews":
            return {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
        if tool_name == "detect_sales_anomaly":
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "threshold_pct": 40.0,
            }
        return {"date": target_date.isoformat()}
