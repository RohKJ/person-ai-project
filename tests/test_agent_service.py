from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from app.agent.errors import AgentConfigurationError
from app.agent.service import AgentService


class FakeResponses:
    def __init__(self) -> None:
        self.create_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.create_kwargs = kwargs
        return SimpleNamespace(
            id="resp_test",
            output=[
                SimpleNamespace(
                    type="function_call",
                    name="fake_tool",
                    arguments=json.dumps({"date": "2026-06-08"}),
                    call_id="call_test",
                )
            ],
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


@dataclass
class FakeTool:
    name: str = "fake_tool"
    description: str = "Fake grounded analysis tool"

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        return args


class FakeRegistry:
    def __init__(self) -> None:
        self.tool = FakeTool()

    def openai_responses_tool_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "name": "fake_tool",
                "description": "Fake grounded analysis tool",
                "parameters": {
                    "type": "object",
                    "properties": {"date": {"type": "string"}},
                    "required": ["date"],
                    "additionalProperties": False,
                },
                "strict": True,
            }
        ]

    def get(self, tool_name: str) -> FakeTool:
        assert tool_name == "fake_tool"
        return self.tool

    def run(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        assert tool_name == "fake_tool"
        return {"metrics": {"grounded_sales": 1234}, "parameters": args}

    def format_answer(self, tool_name: str, result: dict[str, Any]) -> str:
        assert tool_name == "fake_tool"
        return f"Grounded sales: {result['metrics']['grounded_sales']}"


def test_auto_mode_uses_mock_without_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")

    service = AgentService(mode="auto", today=date(2026, 6, 8))

    assert service.status()["resolved_mode"] == "mock"


def test_openai_mode_requires_api_key_or_injected_client(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")

    with pytest.raises(AgentConfigurationError):
        AgentService(mode="openai")


def test_openai_provider_uses_model_only_for_tool_selection(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client = FakeOpenAIClient()
    service = AgentService(
        mode="openai",
        model="test-model",
        today=date(2026, 6, 8),
        registry=FakeRegistry(),  # type: ignore[arg-type]
        openai_client=client,
    )

    response = service.run("오늘 매출 알려줘")

    assert response["provider"] == "openai"
    assert response["tool_name"] == "fake_tool"
    assert response["tool_args"] == {"date": "2026-06-08"}
    assert response["answer"] == "Grounded sales: 1234"
    assert client.responses.create_kwargs["tool_choice"] == "required"
    assert client.responses.create_kwargs["parallel_tool_calls"] is False
