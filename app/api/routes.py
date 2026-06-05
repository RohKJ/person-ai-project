from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.agent.router import AgentRouter
from app.agent.schemas import AgentQueryRequest, AgentQueryResponse
from app.analysis.ads import get_campaign_performance
from app.analysis.inventory import check_inventory_risk
from app.analysis.reviews import summarize_reviews
from app.analysis.sales import get_daily_sales_summary
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


@router.post("/agent/query", response_model=AgentQueryResponse)
def agent_query(request: AgentQueryRequest) -> dict:
    agent = AgentRouter()
    return agent.run(request.query)
