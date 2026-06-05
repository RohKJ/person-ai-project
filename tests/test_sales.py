from app.analysis.sales import calculate_change_rate


def test_daily_sales_change_rate() -> None:
    assert calculate_change_rate(current_value=120_000, previous_value=100_000) == 20.0
    assert calculate_change_rate(current_value=80_000, previous_value=100_000) == -20.0


def test_daily_sales_change_rate_handles_zero_previous_value() -> None:
    assert calculate_change_rate(current_value=80_000, previous_value=0) is None
