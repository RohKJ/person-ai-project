from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.ads import get_campaign_performance
from app.analysis.inventory import check_inventory_risk
from app.analysis.reviews import summarize_reviews
from app.analysis.sales import get_daily_sales_trend
from dashboard.common import configure_page, default_period, format_money, records_to_dataframe
import streamlit as st

configure_page("D2C Operations AI Agent")

st_title = "D2C Operations AI Agent"

st.title(st_title)

start_date, end_date = default_period(7)
sales = get_daily_sales_trend(start_date.isoformat(), end_date.isoformat())
ads = get_campaign_performance(start_date.isoformat(), end_date.isoformat())
inventory = check_inventory_risk(days=7)
reviews = summarize_reviews(start_date.isoformat(), end_date.isoformat())

sales_df = records_to_dataframe(sales["evidence"])
ads_df = records_to_dataframe(ads["evidence"])

total_sales = float(sales_df["total_sales"].sum()) if not sales_df.empty else 0
total_spend = float(ads_df["spend"].sum()) if not ads_df.empty else 0
total_attributed_sales = float(ads_df["attributed_sales"].sum()) if not ads_df.empty else 0
roas = round(total_attributed_sales / total_spend, 2) if total_spend else None

cols = st.columns(5)
cols[0].metric("총매출", format_money(total_sales))
cols[1].metric("광고비", format_money(total_spend))
cols[2].metric("ROAS", roas if roas is not None else "N/A")
cols[3].metric("재고 위험 상품", f"{len(inventory['risk_items'])}개")
cols[4].metric("부정 리뷰", f"{reviews['metrics']['negative_review_count']}건")

left, right = st.columns(2)
with left:
    st.subheader("일별 매출")
    if not sales_df.empty:
        st.line_chart(sales_df.set_index("order_date")["total_sales"])
    else:
        st.info("표시할 매출 데이터가 없습니다.")

with right:
    st.subheader("캠페인 ROAS")
    if not ads_df.empty:
        chart_df = ads_df[["campaign_name", "roas"]].set_index("campaign_name")
        st.bar_chart(chart_df)
    else:
        st.info("표시할 광고 데이터가 없습니다.")
