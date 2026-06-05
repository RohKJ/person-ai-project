# Prompt Test & Learn Log

This document tracks prompt and agent-routing experiments for the D2C operations AI agent.

## Experiment Log

| Date | Prompt / Query | Expected Tool | Actual Tool | Result | Learning |
| --- | --- | --- | --- | --- | --- |
| TBD | 어제 매출 요약해줘 | get_daily_sales_summary | TBD | TBD | Verify relative date handling. |
| TBD | 이번 주 광고 성과 알려줘 | get_campaign_performance | TBD | TBD | Check week boundary logic. |
| TBD | 이번 주 매출 급락 상품 찾아줘 | detect_sales_anomaly | TBD | TBD | Confirm anomaly routing before default sales routing. |
| TBD | 품절 위험 상품 있어? | check_inventory_risk | TBD | TBD | Confirm evidence includes stock and avg sales. |
| TBD | 리뷰 불만사항 정리해줘 | summarize_reviews | TBD | TBD | Improve complaint keyword rules. |
| TBD | 오늘 슬랙 보고서 만들어줘 | generate_slack_report | TBD | TBD | Validate report uses only tool results. |

## Guardrails

- Numeric answers must come from analysis tool outputs.
- Agent responses should expose the tool name, arguments, formula, and evidence.
- Registered tools should expose a Pydantic argument schema.
- Mock mode must work without an OpenAI API key.
- Future LLM mode should convert user intent into tool calls, not generate metric values directly.
