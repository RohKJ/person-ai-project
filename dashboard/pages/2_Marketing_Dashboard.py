from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.ads import get_campaign_performance
from dashboard.common import (
    ALERT,
    ACCENT,
    alert_box,
    configure_page,
    format_compact_money,
    format_pct,
    horizontal_bar_chart,
    page_header,
    period_filter,
    records_to_dataframe,
    section_header,
    show_formula_and_evidence,
    sidebar_context,
)

configure_page("Marketing Dashboard")
sidebar_context()

with st.sidebar:
    selected_start, selected_end = period_filter(
        "광고 분석 기간",
        default_days=14,
        key="marketing_period",
        dataset="ads",
    )
    roas_target = st.number_input("ROAS 목표", min_value=0.0, max_value=20.0, value=2.5, step=0.1)

result = get_campaign_performance(selected_start.isoformat(), selected_end.isoformat())
ads_df = records_to_dataframe(result["evidence"])

total_spend = float(ads_df["spend"].sum()) if not ads_df.empty else 0
total_sales = float(ads_df["attributed_sales"].sum()) if not ads_df.empty else 0
total_clicks = int(ads_df["clicks"].sum()) if not ads_df.empty else 0
total_impressions = int(ads_df["impressions"].sum()) if not ads_df.empty else 0
total_conversions = int(ads_df["conversions"].sum()) if not ads_df.empty else 0
roas = total_sales / total_spend if total_spend else None
ctr = total_clicks / total_impressions * 100 if total_impressions else None
cvr = total_conversions / total_clicks * 100 if total_clicks else None
cpa = total_spend / total_conversions if total_conversions else None

page_header(
    "Marketing Dashboard",
    f"{selected_start.isoformat()} ~ {selected_end.isoformat()} | Campaign efficiency and budget allocation",
)

cols = st.columns(5)
cols[0].metric("광고비", format_compact_money(total_spend))
cols[1].metric("광고 기여 매출", format_compact_money(total_sales))
cols[2].metric("통합 ROAS", f"{roas:.2f}" if roas is not None else "N/A")
cols[3].metric("통합 CTR", format_pct(ctr))
cols[4].metric("CPA", format_compact_money(cpa))

below_target_df = ads_df[ads_df["roas"] < roas_target] if not ads_df.empty else ads_df
if not below_target_df.empty:
    alert_box(f"ROAS 목표 {roas_target:.1f} 미만 캠페인이 {len(below_target_df)}개 있습니다.")

left, right = st.columns(2)
with left:
    section_header("Budget by Campaign")
    if not ads_df.empty:
        horizontal_bar_chart(ads_df, "campaign_name", "spend", "광고비", color=ACCENT)
with right:
    section_header("ROAS by Campaign")
    if not ads_df.empty:
        horizontal_bar_chart(ads_df, "campaign_name", "roas", "ROAS", color=ALERT, value_format=".2f")

section_header("Campaign Performance")
if ads_df.empty:
    st.info("선택 기간의 광고 데이터가 없습니다.")
else:
    st.dataframe(
        ads_df[
            [
                "campaign_name",
                "spend",
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
        column_config={
            "campaign_name": "캠페인",
            "spend": st.column_config.NumberColumn("광고비", format="₩%d"),
            "clicks": st.column_config.NumberColumn("클릭", format="%d"),
            "conversions": st.column_config.NumberColumn("전환", format="%d"),
            "attributed_sales": st.column_config.NumberColumn("기여 매출", format="₩%d"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f"),
            "ctr_pct": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "cvr_pct": st.column_config.NumberColumn("CVR", format="%.2f%%"),
        },
    )

show_formula_and_evidence(result)
