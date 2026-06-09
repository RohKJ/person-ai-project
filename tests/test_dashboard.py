from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


DASHBOARD_PAGES = [
    Path("dashboard/Home.py"),
    Path("dashboard/pages/1_Sales_Dashboard.py"),
    Path("dashboard/pages/2_Marketing_Dashboard.py"),
    Path("dashboard/pages/3_Inventory_Dashboard.py"),
    Path("dashboard/pages/4_Review_VOC_Dashboard.py"),
    Path("dashboard/pages/5_AI_Agent_Report.py"),
]


@pytest.mark.parametrize("page", DASHBOARD_PAGES, ids=lambda page: page.stem)
def test_dashboard_page_renders_without_exception(page: Path) -> None:
    app = AppTest.from_file(str(page), default_timeout=30).run()

    assert not app.exception
