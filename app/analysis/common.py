from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd
from sqlalchemy import text

from app.core.database import engine


def parse_date(value: str | date | None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def date_to_str(value: str | date | None) -> str:
    return parse_date(value).isoformat()


def read_sql(query: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    with engine.connect() as connection:
        return pd.read_sql_query(text(query), connection, params=params or {})


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def dataframe_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    if dataframe.empty:
        return []
    cleaned = dataframe.where(pd.notna(dataframe), None)
    return cleaned.to_dict(orient="records")
