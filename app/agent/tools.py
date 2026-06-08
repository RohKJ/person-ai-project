from __future__ import annotations

from copy import deepcopy
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.agent.formatters import (
    format_campaign_performance_answer,
    format_daily_sales_answer,
    format_inventory_risk_answer,
    format_review_summary_answer,
    format_sales_anomaly_answer,
    format_slack_report_answer,
)
from app.agent.tool_schemas import (
    CampaignPerformanceArgs,
    DailySalesArgs,
    InventoryRiskArgs,
    ReviewSummaryArgs,
    SalesAnomalyArgs,
    SlackReportArgs,
)
from app.analysis.ads import get_campaign_performance
from app.analysis.inventory import check_inventory_risk
from app.analysis.reports import generate_slack_report
from app.analysis.reviews import summarize_reviews
from app.analysis.sales import detect_sales_anomaly, get_daily_sales_summary


ToolHandler = Callable[..., dict[str, Any]]
AnswerFormatter = Callable[[dict[str, Any]], str]


@dataclass(frozen=True)
class AgentTool:
    name: str
    description: str
    args_model: type[BaseModel]
    handler: ToolHandler
    answer_formatter: AnswerFormatter
    keywords: tuple[str, ...] = ()
    default: bool = False

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.args_model(**args).model_dump(exclude_none=True)

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        validated_args = self.validate_args(args)
        return self.handler(**validated_args)

    def format_answer(self, result: dict[str, Any]) -> str:
        return self.answer_formatter(result)

    def openai_responses_tool_schema(self) -> dict[str, Any]:
        parameters = deepcopy(self.args_model.model_json_schema())
        properties = parameters.get("properties", {})
        for property_schema in properties.values():
            property_schema.pop("default", None)
            property_schema.pop("title", None)

        parameters["required"] = list(properties)
        parameters["additionalProperties"] = False
        parameters.pop("title", None)

        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
            "strict": True,
        }


AGENT_TOOLS: tuple[AgentTool, ...] = (
    AgentTool(
        name="generate_slack_report",
        description="Generate a Slack-ready daily or weekly operations report from sales, ads, inventory, and review tools.",
        args_model=SlackReportArgs,
        handler=generate_slack_report,
        answer_formatter=format_slack_report_answer,
        keywords=("슬랙", "보고서", "리포트", "report"),
    ),
    AgentTool(
        name="get_campaign_performance",
        description="Analyze campaign spend, clicks, conversions, attributed sales, ROAS, CTR, and CVR for a date range.",
        args_model=CampaignPerformanceArgs,
        handler=get_campaign_performance,
        answer_formatter=format_campaign_performance_answer,
        keywords=("광고", "캠페인", "roas", "ctr", "cvr", "marketing"),
    ),
    AgentTool(
        name="check_inventory_risk",
        description="Detect products below safety stock or likely to stock out within the selected horizon.",
        args_model=InventoryRiskArgs,
        handler=check_inventory_risk,
        answer_formatter=format_inventory_risk_answer,
        keywords=("품절", "재고", "소진", "안전재고", "inventory"),
    ),
    AgentTool(
        name="summarize_reviews",
        description="Summarize review and VOC quality signals, including average rating, negative reviews, and complaint keywords.",
        args_model=ReviewSummaryArgs,
        handler=summarize_reviews,
        answer_formatter=format_review_summary_answer,
        keywords=("리뷰", "불만", "voc", "cs", "고객", "문의", "review"),
    ),
    AgentTool(
        name="detect_sales_anomaly",
        description="Compare current-period sales with the previous same-length period and detect product-level surges or drops.",
        args_model=SalesAnomalyArgs,
        handler=detect_sales_anomaly,
        answer_formatter=format_sales_anomaly_answer,
        keywords=("이상", "급락", "급등", "하락", "상승", "anomaly"),
    ),
    AgentTool(
        name="get_daily_sales_summary",
        description="Summarize total sales, order count, quantity sold, and previous-day sales change for one date.",
        args_model=DailySalesArgs,
        handler=get_daily_sales_summary,
        answer_formatter=format_daily_sales_answer,
        keywords=("매출", "주문", "판매", "sales"),
        default=True,
    ),
)
