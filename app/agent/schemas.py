from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language operations question")


class AgentQueryResponse(BaseModel):
    query: str
    mode: str
    answer: str
    tool_name: str
    tool_description: str
    tool_args: dict[str, Any]
    route_reason: str
    result: dict[str, Any]
