from __future__ import annotations

from app.analysis.common import dataframe_records, date_to_str, read_sql, round_or_none, safe_divide


def calculate_roas(attributed_sales: float, spend: float) -> float | None:
    return round_or_none(safe_divide(attributed_sales, spend), 2)


def calculate_ctr(clicks: float, impressions: float) -> float | None:
    ratio = safe_divide(clicks, impressions)
    if ratio is None:
        return None
    return round(ratio * 100, 2)


def calculate_cvr(conversions: float, clicks: float) -> float | None:
    ratio = safe_divide(conversions, clicks)
    if ratio is None:
        return None
    return round(ratio * 100, 2)


def get_campaign_performance(start_date: str, end_date: str) -> dict:
    start = date_to_str(start_date)
    end = date_to_str(end_date)
    query = """
        SELECT
            campaign_id,
            campaign_name,
            product_id,
            ROUND(SUM(spend), 2) AS spend,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks,
            SUM(conversions) AS conversions,
            ROUND(SUM(attributed_sales), 2) AS attributed_sales
        FROM ads
        WHERE ad_date BETWEEN :start_date AND :end_date
        GROUP BY campaign_id, campaign_name, product_id
        ORDER BY spend DESC
    """
    dataframe = read_sql(query, {"start_date": start, "end_date": end})
    if not dataframe.empty:
        dataframe["roas"] = dataframe.apply(
            lambda row: calculate_roas(float(row["attributed_sales"]), float(row["spend"])),
            axis=1,
        )
        dataframe["ctr_pct"] = dataframe.apply(
            lambda row: calculate_ctr(float(row["clicks"]), float(row["impressions"])),
            axis=1,
        )
        dataframe["cvr_pct"] = dataframe.apply(
            lambda row: calculate_cvr(float(row["conversions"]), float(row["clicks"])),
            axis=1,
        )

    return {
        "tool_name": "get_campaign_performance",
        "parameters": {"start_date": start, "end_date": end},
        "formula": {
            "roas": "SUM(attributed_sales) / SUM(spend)",
            "ctr_pct": "SUM(clicks) / SUM(impressions) * 100",
            "cvr_pct": "SUM(conversions) / SUM(clicks) * 100",
        },
        "evidence": dataframe_records(dataframe),
    }
