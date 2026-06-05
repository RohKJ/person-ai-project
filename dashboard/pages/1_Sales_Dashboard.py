from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.sales import get_daily_sales_summary, get_daily_sales_trend, get_product_sales
from dashboard.common import configure_page, default_period, format_money, records_to_dataframe, show_formula_and_evidence

configure_page("Sales Dashboard")
st.title("Sales Dashboard")

start_date, end_date = default_period(14)
selected_start, selected_end = st.date_input(
    "기간",
    value=(start_date, end_date),
)

trend = get_daily_sales_trend(selected_start.isoformat(), selected_end.isoformat())
product_sales = get_product_sales(selected_start.isoformat(), selected_end.isoformat())
daily_summary = get_daily_sales_summary(selected_end.isoformat())

metrics = daily_summary["metrics"]
cols = st.columns(4)
cols[0].metric("선택 종료일 매출", format_money(metrics["total_sales"]))
cols[1].metric("주문수", f"{metrics['order_count']:,}건")
cols[2].metric("판매수량", f"{metrics['total_quantity']:,}개")
cols[3].metric("전일 대비", "N/A" if metrics["sales_change_rate_pct"] is None else f"{metrics['sales_change_rate_pct']:+.2f}%")

trend_df = records_to_dataframe(trend["evidence"])
product_df = records_to_dataframe(product_sales["evidence"])

st.subheader("일별 매출 추이")
if not trend_df.empty:
    st.line_chart(trend_df.set_index("order_date")["total_sales"])
    st.dataframe(trend_df, use_container_width=True, hide_index=True)

st.subheader("상품별 매출")
if not product_df.empty:
    st.bar_chart(product_df.set_index("product_name")["total_sales"])
    st.dataframe(product_df, use_container_width=True, hide_index=True)

show_formula_and_evidence(daily_summary)
