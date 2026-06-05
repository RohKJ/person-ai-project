from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.analysis.ads import get_campaign_performance
from app.analysis.inventory import check_inventory_risk
from app.analysis.reports import generate_slack_report
from app.analysis.reviews import summarize_reviews
from app.analysis.sales import get_daily_sales_summary


def _money(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.0f}원"


def _pct(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):+.2f}%"


@dataclass
class RouteDecision:
    tool_name: str
    tool_args: dict[str, Any]


class AgentRouter:
    """Rule-based mock agent router.

    The router chooses an analysis tool from natural language, then formats only
    values returned by that tool. This keeps numeric facts grounded in SQL-backed
    analysis functions and leaves a clean extension point for OpenAI/LangGraph.
    """

    def __init__(self, mode: str | None = None, today: date | None = None) -> None:
        self.mode = mode or os.getenv("AGENT_MODE", "mock")
        self.today = today or date.today()

    def route(self, query: str) -> RouteDecision:
        normalized = query.strip().lower()
        target_date = self._extract_target_date(normalized)
        start_date, end_date = self._extract_period(normalized)

        if any(keyword in normalized for keyword in ["슬랙", "보고서", "리포트"]):
            return RouteDecision(
                "generate_slack_report",
                {
                    "report_type": "daily",
                    "date": target_date.isoformat(),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

        if any(keyword in normalized for keyword in ["광고", "캠페인", "roas", "ctr", "cvr"]):
            return RouteDecision(
                "get_campaign_performance",
                {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            )

        if any(keyword in normalized for keyword in ["품절", "재고", "소진"]):
            return RouteDecision("check_inventory_risk", {"days": 7})

        if any(keyword in normalized for keyword in ["리뷰", "불만", "voc", "cs", "고객"]):
            return RouteDecision(
                "summarize_reviews",
                {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            )

        return RouteDecision("get_daily_sales_summary", {"date": target_date.isoformat()})

    def run(self, query: str) -> dict[str, Any]:
        decision = self.route(query)
        result = self._call_tool(decision)
        return {
            "query": query,
            "mode": self.mode,
            "answer": self._format_answer(decision.tool_name, result),
            "tool_name": decision.tool_name,
            "tool_args": decision.tool_args,
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

    def _call_tool(self, decision: RouteDecision) -> dict[str, Any]:
        if decision.tool_name == "get_daily_sales_summary":
            return get_daily_sales_summary(**decision.tool_args)
        if decision.tool_name == "get_campaign_performance":
            return get_campaign_performance(**decision.tool_args)
        if decision.tool_name == "check_inventory_risk":
            return check_inventory_risk(**decision.tool_args)
        if decision.tool_name == "summarize_reviews":
            return summarize_reviews(**decision.tool_args)
        if decision.tool_name == "generate_slack_report":
            return generate_slack_report(**decision.tool_args)
        raise ValueError(f"Unsupported tool: {decision.tool_name}")

    def _format_answer(self, tool_name: str, result: dict[str, Any]) -> str:
        if tool_name == "get_daily_sales_summary":
            metrics = result["metrics"]
            return (
                f"{result['parameters']['date']} 매출은 {_money(metrics['total_sales'])}, "
                f"주문 {metrics['order_count']:,}건, 판매수량 {metrics['total_quantity']:,}개입니다. "
                f"전일 대비 매출 증감률은 {_pct(metrics['sales_change_rate_pct'])}입니다."
            )

        if tool_name == "get_campaign_performance":
            rows = result["evidence"]
            spend = sum(float(row["spend"]) for row in rows)
            sales = sum(float(row["attributed_sales"]) for row in rows)
            roas = round(sales / spend, 2) if spend else None
            top = max(rows, key=lambda row: float(row["attributed_sales"])) if rows else None
            top_text = f" 최고 기여 매출 캠페인은 {top['campaign_name']}입니다." if top else ""
            return (
                f"{result['parameters']['start_date']}~{result['parameters']['end_date']} 광고비는 {_money(spend)}, "
                f"광고 기여 매출은 {_money(sales)}, 통합 ROAS는 {roas if roas is not None else 'N/A'}입니다."
                f"{top_text}"
            )

        if tool_name == "check_inventory_risk":
            risk_count = len(result["risk_items"])
            names = ", ".join(row["product_name"] for row in result["risk_items"][:3]) or "없음"
            return f"재고 리스크 상품은 {risk_count}개입니다. 우선 확인 대상은 {names}입니다."

        if tool_name == "summarize_reviews":
            metrics = result["metrics"]
            keywords = ", ".join(
                f"{row['keyword']}({row['count']})" for row in result["complaint_keywords"][:3]
            ) or "없음"
            return (
                f"평균 평점은 {metrics['average_rating']}, 부정 리뷰는 {metrics['negative_review_count']}건입니다. "
                f"주요 불만 키워드는 {keywords}입니다."
            )

        if tool_name == "generate_slack_report":
            return result["report_text"]

        return "지원하지 않는 요청입니다."
