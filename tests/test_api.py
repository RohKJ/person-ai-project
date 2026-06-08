from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agent_tools_endpoint_exposes_registry() -> None:
    client = TestClient(app)
    response = client.get("/agent/tools")

    assert response.status_code == 200
    payload = response.json()
    tool_names = {tool["name"] for tool in payload["tools"]}

    assert "get_daily_sales_summary" in tool_names
    assert "detect_sales_anomaly" in tool_names
    assert len(payload["openai_responses_tool_schemas"]) == len(payload["tools"])


def test_agent_status_defaults_to_mock_without_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client = TestClient(app)
    response = client.get("/agent/status")

    assert response.status_code == 200
    assert response.json()["resolved_mode"] == "mock"
