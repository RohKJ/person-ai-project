from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.agent.errors import AgentError
from app.agent.evaluation import evaluate_cases, load_eval_cases
from app.agent.registry import DEFAULT_TOOL_REGISTRY
from app.agent.schemas import AgentQueryRequest, AgentQueryResponse
from app.agent.service import AgentService
from app.analysis.ads import get_campaign_performance
from app.analysis.inventory import check_inventory_risk
from app.analysis.reviews import summarize_reviews
from app.analysis.sales import detect_sales_anomaly, get_daily_sales_summary
from app.core.config import DB_PATH


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "database_exists": DB_PATH.exists(),
        "database_path": str(DB_PATH),
    }


@router.get("/sales/daily")
def sales_daily(target_date: str = Query(default_factory=lambda: date.today().isoformat(), alias="date")) -> dict:
    return get_daily_sales_summary(target_date)


@router.get("/sales/anomaly")
def sales_anomaly(
    start_date: str = Query(default_factory=lambda: (date.today() - timedelta(days=6)).isoformat()),
    end_date: str = Query(default_factory=lambda: date.today().isoformat()),
    threshold_pct: float = 40.0,
) -> dict:
    return detect_sales_anomaly(start_date, end_date, threshold_pct=threshold_pct)


@router.get("/ads/performance")
def ads_performance(
    start_date: str = Query(default_factory=lambda: (date.today() - timedelta(days=6)).isoformat()),
    end_date: str = Query(default_factory=lambda: date.today().isoformat()),
) -> dict:
    return get_campaign_performance(start_date, end_date)


@router.get("/inventory/risk")
def inventory_risk(days: int = 7) -> dict:
    return check_inventory_risk(days=days)


@router.get("/reviews/summary")
def reviews_summary(
    start_date: str = Query(default_factory=lambda: (date.today() - timedelta(days=6)).isoformat()),
    end_date: str = Query(default_factory=lambda: date.today().isoformat()),
) -> dict:
    return summarize_reviews(start_date, end_date)


@router.get("/agent/tools")
def agent_tools() -> dict:
    return {
        "tools": DEFAULT_TOOL_REGISTRY.list_tools(),
        "openai_responses_tool_schemas": DEFAULT_TOOL_REGISTRY.openai_responses_tool_schemas(),
    }


@router.get("/agent/status")
def agent_status() -> dict:
    try:
        return AgentService().status()
    except AgentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/agent/evaluation")
def agent_evaluation(
    mode: str = Query(
        "mock",
        pattern="^(mock|auto|openai)$",
        description="Provider mode used while running the evaluation dataset.",
    ),
) -> dict:
    try:
        return evaluate_cases(load_eval_cases(), mode=mode)
    except AgentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/agent/query", response_model=AgentQueryResponse)
def agent_query(request: AgentQueryRequest) -> dict:
    try:
        agent = AgentService(mode=request.mode)
        return agent.run(request.query)
    except AgentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
