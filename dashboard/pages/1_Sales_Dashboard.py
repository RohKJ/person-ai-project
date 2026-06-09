from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.sales import (
    detect_sales_anomaly,
    get_daily_sales_summary,
    get_daily_sales_trend,
    get_product_sales,
)
from dashboard.common import (
    alert_box,
    configure_page,
    format_compact_money,
    format_number,
    horizontal_bar_chart,
    line_chart,
    metric_delta,
    page_header,
    period_filter,
    records_to_dataframe,
    show_formula_and_evidence,
    sidebar_context,
)

configure_page("Sales Dashboard")
sidebar_context()

with st.sidebar:
    selected_start, selected_end = period_filter("매출 분석 기간", default_days=14, key="sales_period")
    anomaly_threshold = st.slider("이상 탐지 기준", min_value=10, max_value=100, value=40, step=5, format="%d%%")

trend = get_daily_sales_trend(selected_start.isoformat(), selected_end.isoformat())
product_sales = get_product_sales(selected_start.isoformat(), selected_end.isoformat())
daily_summary = get_daily_sales_summary(selected_end.isoformat())
anomalies = detect_sales_anomaly(
    selected_start.isoformat(),
    selected_end.isoformat(),
    threshold_pct=float(anomaly_threshold),
)

trend_df = records_to_dataframe(trend["evidence"])
product_df = records_to_dataframe(product_sales["evidence"])
anomaly_df = records_to_dataframe(anomalies["anomalies"])
metrics = daily_summary["metrics"]

period_sales = float(trend_df["total_sales"].sum()) if not trend_df.empty else 0
period_orders = int(trend_df["order_count"].sum()) if not trend_df.empty else 0
period_quantity = int(trend_df["total_quantity"].sum()) if not trend_df.empty else 0
average_order_value = period_sales / period_orders if period_orders else None

page_header(
    "Sales Dashboard",
    f"{selected_start.isoformat()} ~ {selected_end.isoformat()} | Revenue trend, product mix, and anomaly review",
)

cols = st.columns(5)
cols[0].metric("기간 매출", format_compact_money(period_sales))
cols[1].metric("주문수", format_number(period_orders, "건"))
cols[2].metric("판매수량", format_number(period_quantity, "개"))
cols[3].metric("객단가", format_compact_money(average_order_value))
cols[4].metric(
    "종료일 매출",
    format_compact_money(metrics["total_sales"]),
    delta=metric_delta(metrics["sales_change_rate_pct"]),
)

if not anomaly_df.empty:
    alert_box(f"{anomaly_threshold}% 기준 매출 급등/급락 상품 {len(anomaly_df)}개가 탐지됐습니다.")

trend_tab, products_tab, anomaly_tab = st.tabs(["일별 추이", "상품 성과", "이상 탐지"])
with trend_tab:
    if trend_df.empty:
        st.info("선택 기간의 매출 데이터가 없습니다.")
    else:
        line_chart(trend_df, "order_date", "total_sales", "매출")
        st.dataframe(
            trend_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "order_date": "주문일",
                "total_sales": st.column_config.NumberColumn("매출", format="₩%d"),
                "order_count": st.column_config.NumberColumn("주문수", format="%d"),
                "total_quantity": st.column_config.NumberColumn("판매수량", format="%d"),
            },
        )

with products_tab:
    if product_df.empty:
        st.info("선택 기간의 상품 매출 데이터가 없습니다.")
    else:
        horizontal_bar_chart(product_df, "product_name", "total_sales", "상품 매출")
        st.dataframe(
            product_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "product_name": "상품",
                "total_sales": st.column_config.NumberColumn("매출", format="₩%d"),
                "total_quantity": st.column_config.NumberColumn("판매수량", format="%d"),
                "order_count": st.column_config.NumberColumn("주문수", format="%d"),
            },
        )

with anomaly_tab:
    if anomaly_df.empty:
        st.success("선택 기준을 넘는 매출 이상 상품이 없습니다.")
    else:
        st.dataframe(
            anomaly_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "product_name": "상품",
                "current_sales": st.column_config.NumberColumn("현재 기간 매출", format="₩%d"),
                "previous_sales": st.column_config.NumberColumn("이전 기간 매출", format="₩%d"),
                "change_rate_pct": st.column_config.NumberColumn("증감률", format="%+.2f%%"),
                "direction": "판정",
            },
        )

show_formula_and_evidence(daily_summary)
