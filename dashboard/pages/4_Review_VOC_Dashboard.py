from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.reviews import summarize_reviews
from dashboard.common import (
    ALERT,
    AMBER,
    alert_box,
    configure_page,
    format_pct,
    horizontal_bar_chart,
    page_header,
    period_filter,
    records_to_dataframe,
    show_formula_and_evidence,
    sidebar_context,
)

configure_page("Review VOC Dashboard")
sidebar_context()

with st.sidebar:
    selected_start, selected_end = period_filter(
        "VOC 분석 기간",
        default_days=14,
        key="review_period",
        dataset="reviews",
    )

result = summarize_reviews(selected_start.isoformat(), selected_end.isoformat())
metrics = result["metrics"]
keywords_df = records_to_dataframe(result["complaint_keywords"])
negative_df = records_to_dataframe(result["negative_reviews"])
cs_df = records_to_dataframe(result["cs_summary"])

negative_rate = (
    metrics["negative_review_count"] / metrics["review_count"] * 100
    if metrics["review_count"]
    else None
)
open_cs = (
    int(cs_df.loc[cs_df["status"].isin(["open", "pending"]), "message_count"].sum())
    if not cs_df.empty
    else 0
)
top_keyword = keywords_df.iloc[0]["keyword"] if not keywords_df.empty else "없음"

page_header(
    "Review / VOC Dashboard",
    f"{selected_start.isoformat()} ~ {selected_end.isoformat()} | Complaint signals and customer service workload",
)

cols = st.columns(5)
cols[0].metric("평균 평점", metrics["average_rating"] if metrics["average_rating"] is not None else "N/A")
cols[1].metric("리뷰 수", f"{metrics['review_count']}건")
cols[2].metric("부정 리뷰", f"{metrics['negative_review_count']}건")
cols[3].metric("부정 리뷰율", format_pct(negative_rate))
cols[4].metric("미해결 CS", f"{open_cs}건")

if metrics["negative_review_count"]:
    alert_box(f"주요 불만 키워드는 '{top_keyword}'이며 부정 리뷰가 {metrics['negative_review_count']}건 있습니다.")

keyword_tab, reviews_tab, cs_tab = st.tabs(["불만 키워드", "부정 리뷰", "CS 현황"])
with keyword_tab:
    if keywords_df.empty:
        st.success("선택 기간의 주요 불만 키워드가 없습니다.")
    else:
        horizontal_bar_chart(keywords_df, "keyword", "count", "언급 수", color=ALERT)
        st.dataframe(keywords_df, use_container_width=True, hide_index=True)

with reviews_tab:
    if negative_df.empty:
        st.success("선택 기간 내 부정 리뷰가 없습니다.")
    else:
        st.dataframe(
            negative_df[["review_date", "product_name", "rating", "review_text"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "review_date": "리뷰일",
                "product_name": "상품",
                "rating": st.column_config.NumberColumn("평점", format="%d"),
                "review_text": st.column_config.TextColumn("리뷰", width="large"),
            },
        )

with cs_tab:
    if cs_df.empty:
        st.info("선택 기간의 CS 데이터가 없습니다.")
    else:
        cs_category_df = cs_df.groupby("category", as_index=False)["message_count"].sum()
        horizontal_bar_chart(cs_category_df, "category", "message_count", "문의 수", color=AMBER)
        st.dataframe(cs_df, use_container_width=True, hide_index=True)

show_formula_and_evidence(result)
