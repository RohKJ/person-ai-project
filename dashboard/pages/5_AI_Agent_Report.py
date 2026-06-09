from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agent.errors import AgentError
from app.agent.service import AgentService
from dashboard.common import (
    configure_page,
    evidence_dataframe,
    page_header,
    section_header,
    sidebar_context,
)

configure_page("AI Agent Report")
sidebar_context()

with st.sidebar:
    mode = st.segmented_control(
        "Agent Mode",
        options=["auto", "mock", "openai"],
        default="auto",
        key="agent_mode",
    )
    try:
        provider_status = AgentService(mode=mode).status()
        st.metric("Resolved Provider", provider_status["provider"])
        if provider_status["model"]:
            st.caption(provider_status["model"])
    except AgentError as exc:
        st.error(str(exc))

page_header(
    "AI Agent Report",
    "Natural-language operations query with grounded Tool execution trace",
)

examples = [
    "어제 매출 요약해줘",
    "이번 주 광고 성과 알려줘",
    "품절 위험 상품 있어?",
    "리뷰 불만사항 정리해줘",
    "오늘 슬랙 보고서 만들어줘",
]

if "agent_response" not in st.session_state:
    st.session_state.agent_response = None
if "agent_query" not in st.session_state:
    st.session_state.agent_query = None

section_header("Quick Queries")
buttons = st.columns(len(examples))
selected_query = None
for index, example in enumerate(examples):
    if buttons[index].button(example, key=f"example_{index}", use_container_width=True):
        selected_query = example

typed_query = st.chat_input("운영 질문을 입력하세요")
query = typed_query or selected_query

if query:
    try:
        with st.status("Agent 실행 중", expanded=False) as status:
            agent = AgentService(mode=mode)
            response = agent.run(query)
            status.update(label=f"{response['tool_name']} 실행 완료", state="complete")
        st.session_state.agent_query = query
        st.session_state.agent_response = response
    except AgentError as exc:
        st.error(str(exc))

response = st.session_state.agent_response
if response:
    with st.chat_message("user"):
        st.write(st.session_state.agent_query)
    with st.chat_message("assistant"):
        st.write(response["answer"])

    cols = st.columns(3)
    cols[0].metric("Provider", response["provider"])
    cols[1].metric("Tool", response["tool_name"])
    cols[2].metric("Model", response.get("model") or "N/A")

    trace_tab, formula_tab, evidence_tab, raw_tab = st.tabs(
        ["Tool Trace", "계산식", "근거 데이터", "Raw Result"]
    )
    with trace_tab:
        trace_df = pd.DataFrame(
            [
                {"field": "Route reason", "value": response["route_reason"]},
                {"field": "Tool", "value": response["tool_name"]},
                {"field": "Description", "value": response["tool_description"]},
                {"field": "Arguments", "value": str(response["tool_args"])},
            ]
        )
        st.dataframe(trace_df, use_container_width=True, hide_index=True)
        if response.get("planner_metadata"):
            st.json(response["planner_metadata"])

    with formula_tab:
        formula_df = pd.DataFrame(
            [
                {"metric": metric, "calculation": calculation}
                for metric, calculation in response["result"].get("formula", {}).items()
            ]
        )
        if formula_df.empty:
            st.caption("등록된 계산식이 없습니다.")
        else:
            st.dataframe(formula_df, use_container_width=True, hide_index=True)

    with evidence_tab:
        evidence_df = evidence_dataframe(response["result"].get("evidence", {}))
        if evidence_df.empty:
            st.json(response["result"].get("evidence", {}))
        else:
            st.dataframe(evidence_df, use_container_width=True, hide_index=True)

    with raw_tab:
        st.json(response["result"])
