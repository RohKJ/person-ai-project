from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.ads import get_campaign_performance
from dashboard.common import configure_page, default_period, format_money, records_to_dataframe, show_formula_and_evidence

configure_page("Marketing Dashboard")
st.title("Marketing Dashboard")

start_date, end_date = default_period(14)
selected_start, selected_end = st.date_input(
    "기간",
    value=(start_date, end_date),
)

result = get_campaign_performance(selected_start.isoformat(), selected_end.isoformat())
ads_df = records_to_dataframe(result["evidence"])

total_spend = float(ads_df["spend"].sum()) if not ads_df.empty else 0
total_sales = float(ads_df["attributed_sales"].sum()) if not ads_df.empty else 0
roas = round(total_sales / total_spend, 2) if total_spend else None

cols = st.columns(4)
cols[0].metric("광고비", format_money(total_spend))
cols[1].metric("광고 기여 매출", format_money(total_sales))
cols[2].metric("ROAS", roas if roas is not None else "N/A")
cols[3].metric("캠페인 수", f"{len(ads_df)}개")

if not ads_df.empty:
    left, right = st.columns(2)
    with left:
        st.subheader("캠페인별 광고비")
        st.bar_chart(ads_df.set_index("campaign_name")["spend"])
    with right:
        st.subheader("캠페인별 ROAS")
        st.bar_chart(ads_df.set_index("campaign_name")["roas"])

    st.subheader("성과 테이블")
    st.dataframe(
        ads_df[
            [
                "campaign_name",
                "spend",
                "impressions",
                "clicks",
                "conversions",
                "attributed_sales",
                "roas",
                "ctr_pct",
                "cvr_pct",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

show_formula_and_evidence(result)
