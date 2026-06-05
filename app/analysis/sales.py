from __future__ import annotations

from datetime import timedelta

import pandas as pd

from app.analysis.common import dataframe_records, date_to_str, parse_date, read_sql, round_or_none, safe_divide


def calculate_change_rate(current_value: float, previous_value: float) -> float | None:
    ratio = safe_divide(current_value - previous_value, previous_value)
    if ratio is None:
        return None
    return round(ratio * 100, 2)


def _sales_summary_for_date(target_date: str) -> dict[str, float | int | str]:
    query = """
        SELECT
            :target_date AS order_date,
            COALESCE(SUM(sales_amount), 0) AS total_sales,
            COUNT(DISTINCT order_id) AS order_count,
            COALESCE(SUM(quantity), 0) AS total_quantity
        FROM orders
        WHERE order_date = :target_date
    """
    row = read_sql(query, {"target_date": target_date}).iloc[0].to_dict()
    return {
        "order_date": target_date,
        "total_sales": round(float(row["total_sales"]), 2),
        "order_count": int(row["order_count"]),
        "total_quantity": int(row["total_quantity"]),
    }


def get_daily_sales_summary(date: str | None = None) -> dict:
    target_date = parse_date(date)
    previous_date = target_date - timedelta(days=1)
    current = _sales_summary_for_date(target_date.isoformat())
    previous = _sales_summary_for_date(previous_date.isoformat())
    growth_rate = calculate_change_rate(
        float(current["total_sales"]),
        float(previous["total_sales"]),
    )

    return {
        "tool_name": "get_daily_sales_summary",
        "parameters": {"date": target_date.isoformat()},
        "metrics": {
            "total_sales": current["total_sales"],
            "order_count": current["order_count"],
            "total_quantity": current["total_quantity"],
            "previous_day_sales": previous["total_sales"],
            "sales_change_rate_pct": growth_rate,
        },
        "formula": {
            "total_sales": "SUM(orders.sales_amount) WHERE order_date = target date",
            "order_count": "COUNT(DISTINCT orders.order_id) WHERE order_date = target date",
            "total_quantity": "SUM(orders.quantity) WHERE order_date = target date",
            "sales_change_rate_pct": "(target_date_total_sales - previous_day_total_sales) / previous_day_total_sales * 100",
        },
        "evidence": {
            "target_date": current,
            "previous_date": previous,
        },
    }


def get_daily_sales_trend(start_date: str, end_date: str) -> dict:
    start = date_to_str(start_date)
    end = date_to_str(end_date)
    query = """
        SELECT
            order_date,
            ROUND(SUM(sales_amount), 2) AS total_sales,
            COUNT(DISTINCT order_id) AS order_count,
            SUM(quantity) AS total_quantity
        FROM orders
        WHERE order_date BETWEEN :start_date AND :end_date
        GROUP BY order_date
        ORDER BY order_date
    """
    dataframe = read_sql(query, {"start_date": start, "end_date": end})
    return {
        "tool_name": "get_daily_sales_trend",
        "parameters": {"start_date": start, "end_date": end},
        "formula": {
            "daily_total_sales": "SUM(orders.sales_amount) GROUP BY order_date",
        },
        "evidence": dataframe_records(dataframe),
    }


def get_product_sales(start_date: str, end_date: str) -> dict:
    start = date_to_str(start_date)
    end = date_to_str(end_date)
    query = """
        SELECT
            p.product_id,
            p.product_name,
            ROUND(SUM(o.sales_amount), 2) AS total_sales,
            SUM(o.quantity) AS total_quantity,
            COUNT(DISTINCT o.order_id) AS order_count
        FROM orders o
        JOIN products p ON p.product_id = o.product_id
        WHERE o.order_date BETWEEN :start_date AND :end_date
        GROUP BY p.product_id, p.product_name
        ORDER BY total_sales DESC
    """
    dataframe = read_sql(query, {"start_date": start, "end_date": end})
    return {
        "tool_name": "get_product_sales",
        "parameters": {"start_date": start, "end_date": end},
        "formula": {
            "product_sales": "SUM(orders.sales_amount) GROUP BY product_id",
        },
        "evidence": dataframe_records(dataframe),
    }


def detect_sales_anomaly(start_date: str, end_date: str, threshold_pct: float = 40.0) -> dict:
    start = parse_date(start_date)
    end = parse_date(end_date)
    period_days = (end - start).days + 1
    previous_start = start - timedelta(days=period_days)
    previous_end = start - timedelta(days=1)

    current_query = """
        SELECT
            p.product_id,
            p.product_name,
            ROUND(COALESCE(SUM(o.sales_amount), 0), 2) AS current_sales,
            COALESCE(SUM(o.quantity), 0) AS current_quantity
        FROM products p
        LEFT JOIN orders o
            ON o.product_id = p.product_id
            AND o.order_date BETWEEN :start_date AND :end_date
        GROUP BY p.product_id, p.product_name
    """
    previous_query = """
        SELECT
            p.product_id,
            ROUND(COALESCE(SUM(o.sales_amount), 0), 2) AS previous_sales,
            COALESCE(SUM(o.quantity), 0) AS previous_quantity
        FROM products p
        LEFT JOIN orders o
            ON o.product_id = p.product_id
            AND o.order_date BETWEEN :previous_start AND :previous_end
        GROUP BY p.product_id
    """
    current = read_sql(
        current_query,
        {"start_date": start.isoformat(), "end_date": end.isoformat()},
    )
    previous = read_sql(
        previous_query,
        {
            "previous_start": previous_start.isoformat(),
            "previous_end": previous_end.isoformat(),
        },
    )
    dataframe = current.merge(previous, on="product_id", how="left")
    dataframe["change_rate_pct"] = dataframe.apply(
        lambda row: calculate_change_rate(float(row["current_sales"]), float(row["previous_sales"])),
        axis=1,
    )
    dataframe["direction"] = dataframe["change_rate_pct"].apply(
        lambda value: "surge" if value is not None and value >= threshold_pct else "drop" if value is not None and value <= -threshold_pct else "normal"
    )
    anomalies = dataframe[dataframe["direction"].isin(["surge", "drop"])].copy()
    anomalies = anomalies.sort_values("change_rate_pct", key=lambda column: column.abs(), ascending=False)

    return {
        "tool_name": "detect_sales_anomaly",
        "parameters": {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "previous_start_date": previous_start.isoformat(),
            "previous_end_date": previous_end.isoformat(),
            "threshold_pct": threshold_pct,
        },
        "formula": {
            "change_rate_pct": "(current_period_sales - previous_period_sales) / previous_period_sales * 100",
            "anomaly_rule": f"ABS(change_rate_pct) >= {threshold_pct}",
        },
        "anomalies": dataframe_records(anomalies),
        "evidence": dataframe_records(dataframe),
    }
