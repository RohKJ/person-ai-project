from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agent.router import AgentRouter
from dashboard.common import configure_page

configure_page("AI Agent Report")
st.title("AI Agent Report")

examples = [
    "어제 매출 요약해줘",
    "이번 주 광고 성과 알려줘",
    "품절 위험 상품 있어?",
    "리뷰 불만사항 정리해줘",
    "오늘 슬랙 보고서 만들어줘",
]

query = st.text_input("질문", value=examples[0])
run_clicked = st.button("실행", type="primary")

if run_clicked and query:
    agent = AgentRouter()
    response = agent.run(query)

    st.subheader("답변")
    st.write(response["answer"])

    cols = st.columns(2)
    cols[0].metric("Agent Mode", response["mode"])
    cols[1].metric("Tool", response["tool_name"])

    st.caption(response.get("tool_description", ""))
    st.write(f"Route: {response.get('route_reason', 'N/A')}")

    with st.expander("Tool Arguments", expanded=True):
        st.json(response["tool_args"])

    with st.expander("Formula", expanded=True):
        st.json(response["result"].get("formula", {}))

    with st.expander("Evidence", expanded=True):
        st.json(response["result"].get("evidence", {}))
