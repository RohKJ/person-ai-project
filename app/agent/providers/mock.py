from __future__ import annotations

from datetime import date
from typing import Any

from app.agent.registry import ToolRegistry
from app.agent.router import AgentRouter


class MockAgentProvider:
    name = "mock"

    def __init__(self, registry: ToolRegistry, today: date | None = None) -> None:
        self.router = AgentRouter(mode=self.name, today=today, registry=registry)

    def run(self, query: str) -> dict[str, Any]:
        response = self.router.run(query)
        response["provider"] = self.name
        response["model"] = None
        return response
