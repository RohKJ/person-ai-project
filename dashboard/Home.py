from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.ads import get_campaign_performance
from app.analysis.inventory import check_inventory_risk
from app.analysis.reviews import summarize_reviews
from app.analysis.sales import detect_sales_anomaly, get_daily_sales_trend
from dashboard.common import (
    ACCENT,
    alert_box,
    configure_page,
    format_compact_money,
    horizontal_bar_chart,
    line_chart,
    metric_delta,
    page_header,
    period_filter,
    records_to_dataframe,
    section_header,
    sidebar_context,
)

configure_page("D2C Operations Console")
sidebar_context()

with st.sidebar:
    start_date, end_date = period_filter("요약 기간", default_days=7, key="home_period")
    st.caption(f"기준일 {end_date.isoformat()}")

period_days = (end_date - start_date).days + 1
previous_end = start_date - timedelta(days=1)
previous_start = previous_end - timedelta(days=period_days - 1)

sales = get_daily_sales_trend(start_date.isoformat(), end_date.isoformat())
previous_sales = get_daily_sales_trend(previous_start.isoformat(), previous_end.isoformat())
ads = get_campaign_performance(start_date.isoformat(), end_date.isoformat())
inventory = check_inventory_risk(days=7)
reviews = summarize_reviews(start_date.isoformat(), end_date.isoformat())
anomalies = detect_sales_anomaly(start_date.isoformat(), end_date.isoformat())

sales_df = records_to_dataframe(sales["evidence"])
previous_sales_df = records_to_dataframe(previous_sales["evidence"])
ads_df = records_to_dataframe(ads["evidence"])
risk_df = records_to_dataframe(inventory["risk_items"])
anomaly_df = records_to_dataframe(anomalies["anomalies"])

total_sales = float(sales_df["total_sales"].sum()) if not sales_df.empty else 0
previous_total_sales = float(previous_sales_df["total_sales"].sum()) if not previous_sales_df.empty else 0
sales_delta = (
    (total_sales - previous_total_sales) / previous_total_sales * 100
    if previous_total_sales
    else None
)
total_spend = float(ads_df["spend"].sum()) if not ads_df.empty else 0
total_attributed_sales = float(ads_df["attributed_sales"].sum()) if not ads_df.empty else 0
roas = round(total_attributed_sales / total_spend, 2) if total_spend else None
critical_count = int((risk_df["risk_level"] == "critical").sum()) if not risk_df.empty else 0
negative_count = reviews["metrics"]["negative_review_count"]

page_header(
    "Operations Overview",
    f"{start_date.isoformat()} ~ {end_date.isoformat()} | Daily operating signals and action queue",
)

metrics = st.columns(5)
metrics[0].metric("총매출", format_compact_money(total_sales), delta=metric_delta(sales_delta))
metrics[1].metric("광고비", format_compact_money(total_spend))
metrics[2].metric("통합 ROAS", f"{roas:.2f}" if roas is not None else "N/A")
metrics[3].metric("긴급 재고", f"{critical_count}개", delta=f"{len(risk_df)}개 모니터링", delta_color="off")
metrics[4].metric("부정 리뷰", f"{negative_count}건")

section_header("Action Queue")
if critical_count:
    alert_box(f"안전재고 미만 또는 7일 이내 품절 가능성이 높은 상품이 {critical_count}개 있습니다.")
if not anomaly_df.empty:
    alert_box(f"동일 기간 대비 매출 이상 상품이 {len(anomaly_df)}개 탐지됐습니다.")
if critical_count == 0 and anomaly_df.empty:
    alert_box("현재 긴급 운영 이슈가 없습니다.", healthy=True)

left, right = st.columns([1.3, 1])
with left:
    section_header("Daily Sales")
    if sales_df.empty:
        st.info("선택 기간의 매출 데이터가 없습니다.")
    else:
        line_chart(sales_df, "order_date", "total_sales", "매출")

with right:
    section_header("Campaign ROAS")
    if ads_df.empty:
        st.info("선택 기간의 광고 데이터가 없습니다.")
    else:
        horizontal_bar_chart(ads_df, "campaign_name", "roas", "ROAS", color=ACCENT, value_format=".2f")

section_header("Inventory Actions")
if risk_df.empty:
    st.success("현재 모니터링 대상 재고가 없습니다.")
else:
    st.dataframe(
        risk_df[
            [
                "product_name",
                "risk_level",
                "stock_quantity",
                "safety_stock",
                "average_daily_sales",
                "days_until_stockout",
                "recommended_reorder_quantity",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "product_name": "상품",
            "risk_level": "리스크",
            "stock_quantity": st.column_config.NumberColumn("현재 재고", format="%d"),
            "safety_stock": st.column_config.NumberColumn("안전재고", format="%d"),
            "average_daily_sales": st.column_config.NumberColumn("일평균 판매", format="%.2f"),
            "days_until_stockout": st.column_config.NumberColumn("예상 소진일", format="%.1f일"),
            "recommended_reorder_quantity": st.column_config.NumberColumn("권장 발주", format="%d"),
        },
    )
