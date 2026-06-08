from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language operations question")
    mode: Literal["auto", "mock", "openai"] | None = Field(
        default=None,
        description="Optional provider mode override. Defaults to AGENT_MODE.",
    )


class AgentQueryResponse(BaseModel):
    query: str
    mode: str
    requested_mode: str
    provider: str
    model: str | None
    answer: str
    tool_name: str
    tool_description: str
    tool_args: dict[str, Any]
    route_reason: str
    result: dict[str, Any]
    planner_metadata: dict[str, Any] | None = None
