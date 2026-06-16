# Prompt Test & Learn Log

This document tracks prompt and agent-routing experiments for the D2C operations AI agent.

## Experiment Log

| Date | Prompt / Query | Expected Tool | Actual Tool | Result | Learning |
| --- | --- | --- | --- | --- | --- |
| 2026-06-16 | 어제 매출 요약해줘 | get_daily_sales_summary | get_daily_sales_summary | Pass | Relative date template resolved to the DB reference date minus one day. |
| 2026-06-16 | 이번 주 광고 성과 알려줘 | get_campaign_performance | get_campaign_performance | Pass | Week boundary logic is covered by the eval dataset. |
| 2026-06-16 | 이번 주 매출 급락 상품 찾아줘 | detect_sales_anomaly | detect_sales_anomaly | Pass | Anomaly keywords are evaluated before default sales fallback. |
| 2026-06-08 | 품절 위험 상품 있어? | check_inventory_risk | check_inventory_risk | Pass | OpenAI selected `days=7`; final risk count came from the local analysis Tool. |
| 2026-06-16 | 리뷰 불만사항 정리해줘 | summarize_reviews | summarize_reviews | Pass | Grounding check requires metrics, formula, complaint keywords, and evidence. |
| 2026-06-16 | 오늘 슬랙 보고서 만들어줘 | generate_slack_report | generate_slack_report | Pass | Slack report must include evidence from sales, ads, inventory, and reviews tools. |

## Provider Experiments

| Date | Mode | Scenario | Expected | Actual | Learning |
| --- | --- | --- | --- | --- | --- |
| 2026-06-16 | auto | No `OPENAI_API_KEY` | Resolve to Mock provider | Pass | Local-first execution remains test-covered. |
| 2026-06-08 | openai | API Key configured | Model selects exactly one registered Tool | Pass | Responses API selected `check_inventory_risk(days=7)`. |
| 2026-06-16 | mock | Tool result contains metrics | Final answer uses deterministic formatter | Pass | Eval checks that formula and evidence paths exist for every case. |

## Automated Evaluation

Run:

```bash
python scripts/evaluate_agent.py
```

Dataset:

```text
data/evals/agent_eval_cases.jsonl
```

Tracked metrics:

- `tool_accuracy`: correct Tool selected for the user query.
- `argument_accuracy`: expected date, period, and numeric arguments selected.
- `grounding_coverage`: required formula, evidence, and metric paths are present.
- `overall_pass_rate`: all conditions pass for a case.

## Guardrails

- Numeric answers must come from analysis tool outputs.
- Agent responses should expose the tool name, arguments, formula, and evidence.
- Registered tools should expose a Pydantic argument schema.
- Mock mode must work without an OpenAI API key.
- OpenAI mode converts user intent into one Tool call and does not generate metric values directly.
