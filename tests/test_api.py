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
    assert len(payload["openai_tool_schemas"]) == len(payload["tools"])
