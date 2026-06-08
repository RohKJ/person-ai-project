from __future__ import annotations

import os
from datetime import date
from typing import Any

from dotenv import load_dotenv

from app.agent.errors import AgentConfigurationError
from app.agent.providers.mock import MockAgentProvider
from app.agent.providers.openai_responses import OpenAIResponsesProvider
from app.agent.registry import DEFAULT_TOOL_REGISTRY, ToolRegistry


SUPPORTED_AGENT_MODES = {"auto", "mock", "openai"}
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"


class AgentService:
    def __init__(
        self,
        mode: str | None = None,
        model: str | None = None,
        today: date | None = None,
        registry: ToolRegistry | None = None,
        openai_client: Any | None = None,
    ) -> None:
        load_dotenv()
        self.registry = registry or DEFAULT_TOOL_REGISTRY
        self.requested_mode = (mode or os.getenv("AGENT_MODE", "auto")).lower()
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        self.today = today or date.today()

        if self.requested_mode not in SUPPORTED_AGENT_MODES:
            supported = ", ".join(sorted(SUPPORTED_AGENT_MODES))
            raise AgentConfigurationError(
                f"Unsupported AGENT_MODE '{self.requested_mode}'. Use one of: {supported}."
            )

        self.mode = self._resolve_mode()
        self.provider = self._build_provider(openai_client)

    def run(self, query: str) -> dict[str, Any]:
        response = self.provider.run(query)
        response["requested_mode"] = self.requested_mode
        return response

    def status(self) -> dict[str, Any]:
        return {
            "requested_mode": self.requested_mode,
            "resolved_mode": self.mode,
            "provider": self.provider.name,
            "model": self.model if self.mode == "openai" else None,
            "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        }

    def _resolve_mode(self) -> str:
        if self.requested_mode == "auto":
            return "openai" if os.getenv("OPENAI_API_KEY") else "mock"
        return self.requested_mode

    def _build_provider(self, openai_client: Any | None) -> MockAgentProvider | OpenAIResponsesProvider:
        if self.mode == "mock":
            return MockAgentProvider(registry=self.registry, today=self.today)

        if not os.getenv("OPENAI_API_KEY") and openai_client is None:
            raise AgentConfigurationError(
                "AGENT_MODE=openai requires OPENAI_API_KEY. "
                "Set the key or use AGENT_MODE=auto/mock."
            )

        if openai_client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise AgentConfigurationError(
                    "The openai package is required for AGENT_MODE=openai."
                ) from exc
            openai_client = OpenAI()

        return OpenAIResponsesProvider(
            registry=self.registry,
            model=self.model,
            client=openai_client,
            today=self.today,
        )
