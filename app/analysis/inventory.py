from __future__ import annotations

import math
from datetime import timedelta

import pandas as pd

from app.analysis.common import dataframe_records, parse_date, read_sql, round_or_none, safe_divide


def calculate_days_until_stockout(stock_quantity: float, average_daily_sales: float) -> float | None:
    days = safe_divide(stock_quantity, average_daily_sales)
    if days is None:
        return None
    return round(days, 1)


def check_inventory_risk(days: int = 7) -> dict:
    latest_inventory_date_df = read_sql("SELECT MAX(inventory_date) AS latest_date FROM inventory")
    latest_inventory_date = latest_inventory_date_df.iloc[0]["latest_date"]
    if latest_inventory_date is None:
        return {
            "tool_name": "check_inventory_risk",
            "parameters": {"days": days},
            "formula": {},
            "risk_items": [],
            "evidence": [],
        }

    latest = parse_date(str(latest_inventory_date))
    sales_start = latest - timedelta(days=days - 1)
    inventory_query = """
        SELECT
            i.inventory_date,
            i.product_id,
            p.product_name,
            i.stock_quantity,
            i.safety_stock
        FROM inventory i
        JOIN products p ON p.product_id = i.product_id
        WHERE i.inventory_date = :latest_date
    """
    sales_query = """
        SELECT
            product_id,
            COALESCE(SUM(quantity), 0) AS period_quantity
        FROM orders
        WHERE order_date BETWEEN :sales_start AND :latest_date
        GROUP BY product_id
    """
    inventory = read_sql(inventory_query, {"latest_date": latest.isoformat()})
    sales = read_sql(
        sales_query,
        {"sales_start": sales_start.isoformat(), "latest_date": latest.isoformat()},
    )
    dataframe = inventory.merge(sales, on="product_id", how="left")
    dataframe["period_quantity"] = dataframe["period_quantity"].fillna(0)
    dataframe["average_daily_sales"] = dataframe["period_quantity"] / days
    dataframe["days_until_stockout"] = dataframe.apply(
        lambda row: calculate_days_until_stockout(
            float(row["stock_quantity"]),
            float(row["average_daily_sales"]),
        ),
        axis=1,
    )
    dataframe["below_safety_stock"] = dataframe["stock_quantity"] < dataframe["safety_stock"]
    dataframe["stockout_within_days"] = dataframe["days_until_stockout"].apply(
        lambda value: False if value is None or pd.isna(value) else value <= days
    )
    dataframe["risk_level"] = dataframe.apply(
        lambda row: "critical"
        if row["below_safety_stock"] or row["stockout_within_days"]
        else "watch"
        if row["days_until_stockout"] is not None and not pd.isna(row["days_until_stockout"]) and row["days_until_stockout"] <= days * 2
        else "normal",
        axis=1,
    )
    dataframe["recommended_reorder_quantity"] = dataframe.apply(
        lambda row: max(
            0,
            int(math.ceil(float(row["average_daily_sales"]) * 14 + float(row["safety_stock"]) - float(row["stock_quantity"]))),
        ),
        axis=1,
    )
    dataframe["average_daily_sales"] = dataframe["average_daily_sales"].apply(lambda value: round_or_none(value, 2))
    dataframe = dataframe.sort_values(
        ["risk_level", "days_until_stockout"],
        ascending=[True, True],
    )
    risk_items = dataframe[dataframe["risk_level"].isin(["critical", "watch"])]

    return {
        "tool_name": "check_inventory_risk",
        "parameters": {
            "days": days,
            "latest_inventory_date": latest.isoformat(),
            "sales_window_start": sales_start.isoformat(),
        },
        "formula": {
            "average_daily_sales": f"SUM(orders.quantity in latest {days} days) / {days}",
            "days_until_stockout": "stock_quantity / average_daily_sales",
            "risk_rule": "stock_quantity < safety_stock OR days_until_stockout <= days",
        },
        "risk_items": dataframe_records(risk_items),
        "evidence": dataframe_records(dataframe),
    }
