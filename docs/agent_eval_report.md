# Agent Evaluation Report

- Reference date: `2026-06-05` (latest inventory date in SQLite)
- Mode: `mock`
- Total cases: `8`
- Overall pass rate: `100.00%`
- Tool accuracy: `100.00%`
- Argument accuracy: `100.00%`
- Grounding coverage: `100.00%`

| Case | Query | Expected Tool | Actual Tool | Tool | Args | Grounding |
| --- | --- | --- | --- | --- | --- | --- |
| daily_sales_yesterday | 어제 매출 요약해줘 | `get_daily_sales_summary` | `get_daily_sales_summary` | Pass | Pass | Pass |
| campaign_this_week | 이번 주 광고 성과 알려줘 | `get_campaign_performance` | `get_campaign_performance` | Pass | Pass | Pass |
| inventory_default_horizon | 품절 위험 상품 있어? | `check_inventory_risk` | `check_inventory_risk` | Pass | Pass | Pass |
| inventory_14_day_horizon | 최근 14일 재고 소진 위험 상품 알려줘 | `check_inventory_risk` | `check_inventory_risk` | Pass | Pass | Pass |
| review_complaints | 리뷰 불만사항 정리해줘 | `summarize_reviews` | `summarize_reviews` | Pass | Pass | Pass |
| sales_anomaly_this_week | 이번 주 매출 급락 상품 찾아줘 | `detect_sales_anomaly` | `detect_sales_anomaly` | Pass | Pass | Pass |
| slack_daily_report | 오늘 슬랙 보고서 만들어줘 | `generate_slack_report` | `generate_slack_report` | Pass | Pass | Pass |
| default_sales_fallback | 운영 현황 간단히 보여줘 | `get_daily_sales_summary` | `get_daily_sales_summary` | Pass | Pass | Pass |

## Failures

No failures.
