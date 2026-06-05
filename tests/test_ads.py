from app.analysis.ads import calculate_ctr, calculate_cvr, calculate_roas


def test_roas_calculation() -> None:
    assert calculate_roas(attributed_sales=500_000, spend=100_000) == 5.0


def test_rate_calculations_handle_zero_denominator() -> None:
    assert calculate_roas(attributed_sales=100_000, spend=0) is None
    assert calculate_ctr(clicks=10, impressions=0) is None
    assert calculate_cvr(conversions=2, clicks=0) is None
