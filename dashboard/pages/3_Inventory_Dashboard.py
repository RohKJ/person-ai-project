from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.inventory import check_inventory_risk
from dashboard.common import (
    ALERT,
    AMBER,
    alert_box,
    configure_page,
    format_number,
    horizontal_bar_chart,
    page_header,
    records_to_dataframe,
    show_formula_and_evidence,
    sidebar_context,
)

configure_page("Inventory Dashboard")
sidebar_context()

with st.sidebar:
    days = st.slider("품절 위험 기준", min_value=3, max_value=21, value=7, step=1, format="%d일")

result = check_inventory_risk(days=days)
inventory_df = records_to_dataframe(result["evidence"])
risk_df = records_to_dataframe(result["risk_items"])

critical_count = int((inventory_df["risk_level"] == "critical").sum()) if not inventory_df.empty else 0
watch_count = int((inventory_df["risk_level"] == "watch").sum()) if not inventory_df.empty else 0
total_stock = int(inventory_df["stock_quantity"].sum()) if not inventory_df.empty else 0
reorder_quantity = int(risk_df["recommended_reorder_quantity"].sum()) if not risk_df.empty else 0

page_header(
    "Inventory Dashboard",
    f"{result['parameters'].get('latest_inventory_date', 'N/A')} snapshot | {days}-day stockout risk horizon",
)

cols = st.columns(5)
cols[0].metric("전체 상품", format_number(len(inventory_df), "개"))
cols[1].metric("긴급", format_number(critical_count, "개"))
cols[2].metric("관찰", format_number(watch_count, "개"))
cols[3].metric("총 재고", format_number(total_stock, "개"))
cols[4].metric("권장 발주", format_number(reorder_quantity, "개"))

if critical_count:
    alert_box(f"긴급 재고 상품 {critical_count}개를 우선 발주 대상으로 검토해야 합니다.")

risk_tab, coverage_tab, all_tab = st.tabs(["발주 우선순위", "재고 커버리지", "전체 재고"])
with risk_tab:
    if risk_df.empty:
        st.success("현재 모니터링 대상 재고가 없습니다.")
    else:
        st.dataframe(
            risk_df[
                [
                    "product_name",
                    "risk_level",
                    "stock_quantity",
                    "safety_stock",
                    "average_daily_sales",
                    "days_until_stockout",
                    "recommended_reorder_quantity",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "product_name": "상품",
                "risk_level": "리스크",
                "stock_quantity": st.column_config.NumberColumn("현재 재고", format="%d"),
                "safety_stock": st.column_config.NumberColumn("안전재고", format="%d"),
                "average_daily_sales": st.column_config.NumberColumn("일평균 판매", format="%.2f"),
                "days_until_stockout": st.column_config.ProgressColumn(
                    "예상 소진일",
                    min_value=0,
                    max_value=max(days * 2, 14),
                    format="%.1f일",
                ),
                "recommended_reorder_quantity": st.column_config.NumberColumn("권장 발주", format="%d"),
            },
        )

with coverage_tab:
    if not inventory_df.empty:
        horizontal_bar_chart(
            inventory_df.sort_values("days_until_stockout", na_position="last"),
            "product_name",
            "days_until_stockout",
            "예상 소진일",
            color=AMBER,
        )

with all_tab:
    if not inventory_df.empty:
        st.dataframe(inventory_df, use_container_width=True, hide_index=True)

show_formula_and_evidence(result)
