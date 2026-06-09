from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analysis.common import read_sql

ACCENT = "#0F766E"
ALERT = "#B42318"
AMBER = "#B54708"
INK = "#17202A"
MUTED = "#667085"


def configure_page(title: str) -> None:
    st.set_page_config(page_title=title, page_icon="📊", layout="wide")
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: #F7F8FA; }
        [data-testid="stHeader"] { background: rgba(247, 248, 250, 0.92); }
        [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E4E7EC; }
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E4E7EC;
            border-radius: 6px;
            padding: 14px 16px;
            min-height: 110px;
        }
        [data-testid="stMetricLabel"] { color: #667085; }
        [data-testid="stMetricValue"] { color: #17202A; font-size: 1.7rem; overflow: visible; }
        [data-testid="stMetricValue"] > div {
            font-size: 1.7rem;
            overflow: visible;
            text-overflow: clip;
            white-space: nowrap;
        }
        [data-testid="stDataFrame"] { border: 1px solid #E4E7EC; border-radius: 6px; }
        div[data-testid="stExpander"] { border: 1px solid #E4E7EC; border-radius: 6px; }
        .ops-kicker {
            color: #0F766E;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }
        .ops-title {
            color: #17202A;
            font-size: 1.85rem;
            line-height: 1.2;
            font-weight: 700;
            margin: 0;
        }
        .ops-caption {
            color: #667085;
            font-size: 0.9rem;
            margin: 0.35rem 0 1.25rem 0;
        }
        .ops-section {
            color: #17202A;
            font-size: 1.08rem;
            font-weight: 700;
            margin: 1.4rem 0 0.7rem 0;
        }
        .ops-alert {
            background: #FFFFFF;
            border-left: 4px solid #B42318;
            border-top: 1px solid #E4E7EC;
            border-right: 1px solid #E4E7EC;
            border-bottom: 1px solid #E4E7EC;
            border-radius: 4px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.55rem;
            color: #344054;
        }
        .ops-ok {
            background: #FFFFFF;
            border-left: 4px solid #0F766E;
            border-top: 1px solid #E4E7EC;
            border-right: 1px solid #E4E7EC;
            border-bottom: 1px solid #E4E7EC;
            border-radius: 4px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.55rem;
            color: #344054;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, caption: str, kicker: str = "LumaRoot Operations") -> None:
    st.markdown(
        f"""
        <div class="ops-kicker">{kicker}</div>
        <h1 class="ops-title">{title}</h1>
        <p class="ops-caption">{caption}</p>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str) -> None:
    st.markdown(f'<div class="ops-section">{title}</div>', unsafe_allow_html=True)


def sidebar_context() -> None:
    with st.sidebar:
        st.markdown("### LumaRoot")
        st.caption("D2C Operations Console")
        st.divider()


@st.cache_data(ttl=60)
def latest_data_date(dataset: str = "orders") -> date:
    date_columns = {
        "orders": "order_date",
        "ads": "ad_date",
        "inventory": "inventory_date",
        "reviews": "review_date",
        "cs_messages": "message_date",
    }
    if dataset not in date_columns:
        raise ValueError(f"Unsupported dashboard dataset: {dataset}")

    date_column = date_columns[dataset]
    dataframe = read_sql(f"SELECT MAX({date_column}) AS latest_date FROM {dataset}")
    latest = dataframe.iloc[0]["latest_date"] if not dataframe.empty else None
    return pd.to_datetime(latest).date() if latest else date.today()


def default_period(days: int = 7, dataset: str = "orders") -> tuple[date, date]:
    end = latest_data_date(dataset)
    return end - timedelta(days=days - 1), end


def period_filter(
    label: str = "분석 기간",
    default_days: int = 14,
    key: str = "period",
    dataset: str = "orders",
) -> tuple[date, date]:
    default_start, default_end = default_period(default_days, dataset=dataset)
    selected = st.date_input(
        label,
        value=(default_start, default_end),
        key=key,
    )
    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        return selected[0], selected[1]
    return default_start, default_end


def records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(records)


def format_money(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.0f}원"


def format_compact_money(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    amount = float(value)
    if abs(amount) >= 100_000_000:
        return f"₩{amount / 100_000_000:.1f}B"
    if abs(amount) >= 1_000_000:
        return f"₩{amount / 1_000_000:.1f}M"
    if abs(amount) >= 1_000:
        return f"₩{amount / 1_000:.1f}K"
    return f"₩{amount:,.0f}"


def format_number(value: float | int | None, suffix: str = "") -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.0f}{suffix}"


def format_pct(value: float | int | None, signed: bool = False) -> str:
    if value is None:
        return "N/A"
    sign = "+" if signed else ""
    return f"{float(value):{sign}.2f}%"


def metric_delta(value: float | int | None, suffix: str = "%") -> str | None:
    if value is None:
        return None
    return f"{float(value):+.2f}{suffix}"


def alert_box(message: str, healthy: bool = False) -> None:
    css_class = "ops-ok" if healthy else "ops-alert"
    st.markdown(f'<div class="{css_class}">{message}</div>', unsafe_allow_html=True)


def line_chart(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    y_title: str,
    color: str = ACCENT,
) -> None:
    chart = (
        alt.Chart(dataframe)
        .mark_line(point=True, color=color, strokeWidth=2)
        .encode(
            x=alt.X(
                f"{x}:O",
                title=None,
                sort=None,
                axis=alt.Axis(labelAngle=-35, labelExpr="slice(datum.label, 5)"),
            ),
            y=alt.Y(f"{y}:Q", title=y_title, axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip(f"{x}:N", title="Date"),
                alt.Tooltip(f"{y}:Q", title=y_title, format=",.0f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)


def horizontal_bar_chart(
    dataframe: pd.DataFrame,
    category: str,
    value: str,
    value_title: str,
    color: str = ACCENT,
    value_format: str = ",.0f",
) -> None:
    chart = (
        alt.Chart(dataframe)
        .mark_bar(color=color, cornerRadiusEnd=3)
        .encode(
            x=alt.X(f"{value}:Q", title=value_title, axis=alt.Axis(format=value_format)),
            y=alt.Y(f"{category}:N", title=None, sort="-x"),
            tooltip=[
                alt.Tooltip(f"{category}:N", title="Name"),
                alt.Tooltip(f"{value}:Q", title=value_title, format=value_format),
            ],
        )
        .properties(height=max(240, min(420, len(dataframe) * 38)))
    )
    st.altair_chart(chart, use_container_width=True)


def evidence_dataframe(evidence: Any) -> pd.DataFrame:
    if isinstance(evidence, list):
        return records_to_dataframe(evidence)
    if isinstance(evidence, dict):
        rows = []
        for key, value in evidence.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                rows.append({"field": key, "value": value})
        return pd.DataFrame(rows)
    return pd.DataFrame()


def show_formula_and_evidence(result: dict[str, Any]) -> None:
    formula = result.get("formula", {})
    evidence = result.get("evidence", {})
    formula_df = pd.DataFrame(
        [{"metric": metric, "calculation": calculation} for metric, calculation in formula.items()]
    )
    evidence_df = evidence_dataframe(evidence)

    with st.expander("계산식 및 근거 데이터"):
        formula_tab, evidence_tab, raw_tab = st.tabs(["계산식", "근거 테이블", "Raw"])
        with formula_tab:
            if formula_df.empty:
                st.caption("등록된 계산식이 없습니다.")
            else:
                st.dataframe(formula_df, use_container_width=True, hide_index=True)
        with evidence_tab:
            if evidence_df.empty:
                st.caption("표 형태로 표시할 근거 데이터가 없습니다.")
            else:
                st.dataframe(evidence_df, use_container_width=True, hide_index=True)
        with raw_tab:
            st.json(evidence)
