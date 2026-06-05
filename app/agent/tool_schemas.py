from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DailySalesArgs(ToolArgs):
    date: str = Field(..., description="Target date in YYYY-MM-DD format")


class CampaignPerformanceArgs(ToolArgs):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class SalesAnomalyArgs(ToolArgs):
    start_date: str = Field(..., description="Current period start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="Current period end date in YYYY-MM-DD format")
    threshold_pct: float = Field(40.0, ge=0, description="Absolute change rate threshold for anomaly detection")


class InventoryRiskArgs(ToolArgs):
    days: int = Field(7, ge=1, le=365, description="Stockout risk horizon in days")


class ReviewSummaryArgs(ToolArgs):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class SlackReportArgs(ToolArgs):
    report_type: str = Field("daily", description="Report type, such as daily or weekly")
    date: str = Field(..., description="Report target date in YYYY-MM-DD format")
    start_date: str = Field(..., description="Evidence period start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="Evidence period end date in YYYY-MM-DD format")
