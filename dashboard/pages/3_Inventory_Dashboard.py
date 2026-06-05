from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.inventory import check_inventory_risk
from dashboard.common import configure_page, records_to_dataframe, show_formula_and_evidence

configure_page("Inventory Dashboard")
st.title("Inventory Dashboard")

days = st.slider("위험 기준일", min_value=3, max_value=21, value=7, step=1)
result = check_inventory_risk(days=days)
inventory_df = records_to_dataframe(result["evidence"])
risk_df = records_to_dataframe(result["risk_items"])

cols = st.columns(3)
cols[0].metric("전체 상품", f"{len(inventory_df)}개")
cols[1].metric("위험/관찰 상품", f"{len(risk_df)}개")
cols[2].metric("기준일", f"{days}일")

if not inventory_df.empty:
    st.subheader("상품별 재고")
    st.bar_chart(inventory_df.set_index("product_name")["stock_quantity"])
    st.dataframe(inventory_df, use_container_width=True, hide_index=True)

st.subheader("품절 위험 상품")
if not risk_df.empty:
    st.dataframe(risk_df, use_container_width=True, hide_index=True)
else:
    st.success("현재 기준 위험 상품이 없습니다.")

show_formula_and_evidence(result)
