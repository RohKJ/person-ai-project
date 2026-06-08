from datetime import date

from app.agent.registry import DEFAULT_TOOL_REGISTRY
from app.agent.router import AgentRouter


def test_agent_router_sales_yesterday() -> None:
    router = AgentRouter(today=date(2026, 6, 5))
    decision = router.route("어제 매출 요약해줘")

    assert decision.tool_name == "get_daily_sales_summary"
    assert decision.tool_args == {"date": "2026-06-04"}


def test_agent_router_campaign_performance() -> None:
    router = AgentRouter(today=date(2026, 6, 5))
    decision = router.route("이번 주 광고 성과 알려줘")

    assert decision.tool_name == "get_campaign_performance"
    assert decision.tool_args == {"start_date": "2026-06-01", "end_date": "2026-06-05"}


def test_agent_router_inventory_risk() -> None:
    router = AgentRouter(today=date(2026, 6, 5))
    decision = router.route("품절 위험 상품 있어?")

    assert decision.tool_name == "check_inventory_risk"
    assert decision.tool_args == {"days": 7}


def test_agent_router_review_summary() -> None:
    router = AgentRouter(today=date(2026, 6, 5))
    decision = router.route("리뷰 불만사항 정리해줘")

    assert decision.tool_name == "summarize_reviews"


def test_agent_router_slack_report() -> None:
    router = AgentRouter(today=date(2026, 6, 5))
    decision = router.route("오늘 슬랙 보고서 만들어줘")

    assert decision.tool_name == "generate_slack_report"
    assert decision.tool_args["date"] == "2026-06-05"


def test_agent_router_sales_anomaly() -> None:
    router = AgentRouter(today=date(2026, 6, 5))
    decision = router.route("이번 주 매출 급락 상품 찾아줘")

    assert decision.tool_name == "detect_sales_anomaly"
    assert decision.tool_args == {
        "start_date": "2026-06-01",
        "end_date": "2026-06-05",
        "threshold_pct": 40.0,
    }


def test_agent_tool_registry_exposes_tool_schemas() -> None:
    tools = DEFAULT_TOOL_REGISTRY.list_tools()
    schemas = DEFAULT_TOOL_REGISTRY.openai_responses_tool_schemas()
    tool_names = {tool["name"] for tool in tools}
    schema_names = {schema["name"] for schema in schemas}

    assert "get_daily_sales_summary" in tool_names
    assert "detect_sales_anomaly" in tool_names
    assert tool_names == schema_names
    assert all(schema["strict"] is True for schema in schemas)
    assert all(
        schema["parameters"]["required"] == list(schema["parameters"]["properties"])
        for schema in schemas
    )
