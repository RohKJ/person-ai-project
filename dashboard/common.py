from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def configure_page(title: str) -> None:
    st.set_page_config(page_title=title, page_icon="📊", layout="wide")


def default_period(days: int = 7) -> tuple[date, date]:
    end = date.today()
    return end - timedelta(days=days - 1), end


def records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(records)


def format_money(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.0f}원"


def show_formula_and_evidence(result: dict[str, Any]) -> None:
    with st.expander("Formula"):
        st.json(result.get("formula", {}))
    with st.expander("Evidence"):
        st.json(result.get("evidence", {}))
