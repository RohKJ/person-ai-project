from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.reviews import summarize_reviews
from dashboard.common import configure_page, default_period, records_to_dataframe, show_formula_and_evidence

configure_page("Review VOC Dashboard")
st.title("Review/VOC Dashboard")

start_date, end_date = default_period(14)
selected_start, selected_end = st.date_input(
    "기간",
    value=(start_date, end_date),
)

result = summarize_reviews(selected_start.isoformat(), selected_end.isoformat())
metrics = result["metrics"]
keywords_df = records_to_dataframe(result["complaint_keywords"])
negative_df = records_to_dataframe(result["negative_reviews"])
cs_df = records_to_dataframe(result["cs_summary"])

cols = st.columns(3)
cols[0].metric("평균 평점", metrics["average_rating"] if metrics["average_rating"] is not None else "N/A")
cols[1].metric("리뷰 수", f"{metrics['review_count']}건")
cols[2].metric("부정 리뷰", f"{metrics['negative_review_count']}건")

left, right = st.columns(2)
with left:
    st.subheader("주요 불만 키워드")
    if not keywords_df.empty:
        st.bar_chart(keywords_df.set_index("keyword")["count"])
        st.dataframe(keywords_df, use_container_width=True, hide_index=True)

with right:
    st.subheader("CS 카테고리")
    if not cs_df.empty:
        pivot_df = cs_df.pivot_table(index="category", values="message_count", aggfunc="sum")
        st.bar_chart(pivot_df)
        st.dataframe(cs_df, use_container_width=True, hide_index=True)

st.subheader("부정 리뷰")
if not negative_df.empty:
    st.dataframe(
        negative_df[["review_date", "product_name", "rating", "review_text"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success("선택 기간 내 부정 리뷰가 없습니다.")

show_formula_and_evidence(result)
