from datetime import date

from app.agent.evaluation import (
    DEFAULT_CASES_PATH,
    evaluate_cases,
    load_eval_cases,
    resolve_templates,
)


def test_eval_case_templates_resolve_relative_dates() -> None:
    resolved = resolve_templates(
        {
            "date": "{{yesterday}}",
            "start_date": "{{week_start}}",
            "end_date": "{{today}}",
        },
        date(2026, 6, 16),
    )

    assert resolved == {
        "date": "2026-06-15",
        "start_date": "2026-06-15",
        "end_date": "2026-06-16",
    }


def test_mock_agent_evaluation_dataset_passes() -> None:
    cases = load_eval_cases(DEFAULT_CASES_PATH)
    report = evaluate_cases(cases, mode="mock")

    assert report["summary"]["total_cases"] == len(cases)
    assert report["summary"]["overall_pass_rate"] == 1.0
    assert report["summary"]["tool_accuracy"] == 1.0
    assert report["summary"]["argument_accuracy"] == 1.0
    assert report["summary"]["grounding_coverage"] == 1.0
