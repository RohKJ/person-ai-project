from app.analysis.inventory import calculate_days_until_stockout


def test_days_until_stockout_calculation() -> None:
    assert calculate_days_until_stockout(stock_quantity=70, average_daily_sales=10) == 7.0
    assert calculate_days_until_stockout(stock_quantity=75, average_daily_sales=10) == 7.5


def test_days_until_stockout_handles_zero_sales() -> None:
    assert calculate_days_until_stockout(stock_quantity=70, average_daily_sales=0) is None
