from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.agent.service import AgentService
from app.core.config import BASE_DIR, DB_PATH


DEFAULT_CASES_PATH = BASE_DIR / "data" / "evals" / "agent_eval_cases.jsonl"
DEFAULT_JSON_OUTPUT_PATH = BASE_DIR / "reports" / "agent_eval_latest.json"
DEFAULT_MARKDOWN_OUTPUT_PATH = BASE_DIR / "docs" / "agent_eval_report.md"


@dataclass(frozen=True)
class EvalCase:
    id: str
    query: str
    expected_tool: str
    expected_args: dict[str, Any]
    required_response_paths: list[str]


@dataclass(frozen=True)
class CaseResult:
    id: str
    query: str
    expected_tool: str
    actual_tool: str | None
    expected_args: dict[str, Any]
    actual_args: dict[str, Any]
    tool_passed: bool
    args_passed: bool
    grounding_passed: bool
    passed: bool
    missing_paths: list[str]
    route_reason: str | None
    provider: str | None
    error: str | None = None


def load_eval_cases(path: Path = DEFAULT_CASES_PATH) -> list[EvalCase]:
    cases: list[EvalCase] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            case = EvalCase(
                id=payload["id"],
                query=payload["query"],
                expected_tool=payload["expected_tool"],
                expected_args=payload.get("expected_args", {}),
                required_response_paths=payload.get("required_response_paths", []),
            )
            if not case.id:
                raise ValueError(f"Eval case on line {line_number} must include an id.")
            cases.append(case)
    return cases


def infer_reference_date(db_path: Path = DB_PATH) -> date:
    if not db_path.exists():
        return date.today()

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute("SELECT MAX(inventory_date) FROM inventory")
        latest = cursor.fetchone()[0]

    if latest:
        return datetime.strptime(str(latest), "%Y-%m-%d").date()
    return date.today()


def _template_values(reference_date: date) -> dict[str, str]:
    week_start = reference_date - timedelta(days=reference_date.weekday())
    return {
        "{{today}}": reference_date.isoformat(),
        "{{yesterday}}": (reference_date - timedelta(days=1)).isoformat(),
        "{{two_days_ago}}": (reference_date - timedelta(days=2)).isoformat(),
        "{{week_start}}": week_start.isoformat(),
        "{{rolling_7_start}}": (reference_date - timedelta(days=6)).isoformat(),
    }


def resolve_templates(value: Any, reference_date: date) -> Any:
    if isinstance(value, str):
        return _template_values(reference_date).get(value, value)
    if isinstance(value, dict):
        return {key: resolve_templates(item, reference_date) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_templates(item, reference_date) for item in value]
    return value


def get_path(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if 0 <= index < len(current):
                current = current[index]
                continue
        return None
    return current


def is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def expected_args_match(actual_args: dict[str, Any], expected_args: dict[str, Any]) -> bool:
    return all(actual_args.get(key) == expected_value for key, expected_value in expected_args.items())


def evaluate_cases(
    cases: list[EvalCase],
    *,
    mode: str = "mock",
    reference_date: date | None = None,
) -> dict[str, Any]:
    reference_date = reference_date or infer_reference_date()
    service = AgentService(mode=mode, today=reference_date)
    case_results: list[CaseResult] = []

    for case in cases:
        expected_args = resolve_templates(case.expected_args, reference_date)
        required_paths = resolve_templates(case.required_response_paths, reference_date)
        try:
            response = service.run(case.query)
            missing_paths = [
                path for path in required_paths if not is_present(get_path(response, path))
            ]
            actual_tool = response.get("tool_name")
            actual_args = response.get("tool_args", {})
            tool_passed = actual_tool == case.expected_tool
            args_passed = expected_args_match(actual_args, expected_args)
            grounding_passed = not missing_paths
            passed = tool_passed and args_passed and grounding_passed
            case_results.append(
                CaseResult(
                    id=case.id,
                    query=case.query,
                    expected_tool=case.expected_tool,
                    actual_tool=actual_tool,
                    expected_args=expected_args,
                    actual_args=actual_args,
                    tool_passed=tool_passed,
                    args_passed=args_passed,
                    grounding_passed=grounding_passed,
                    passed=passed,
                    missing_paths=missing_paths,
                    route_reason=response.get("route_reason"),
                    provider=response.get("provider"),
                )
            )
        except Exception as exc:  # pragma: no cover - defensive CLI/API reporting
            case_results.append(
                CaseResult(
                    id=case.id,
                    query=case.query,
                    expected_tool=case.expected_tool,
                    actual_tool=None,
                    expected_args=expected_args,
                    actual_args={},
                    tool_passed=False,
                    args_passed=False,
                    grounding_passed=False,
                    passed=False,
                    missing_paths=list(required_paths),
                    route_reason=None,
                    provider=None,
                    error=str(exc),
                )
            )

    total = len(case_results)
    passed_count = sum(result.passed for result in case_results)
    tool_pass_count = sum(result.tool_passed for result in case_results)
    args_pass_count = sum(result.args_passed for result in case_results)
    grounding_pass_count = sum(result.grounding_passed for result in case_results)

    def rate(count: int) -> float:
        return round(count / total, 4) if total else 0.0

    return {
        "reference_date": reference_date.isoformat(),
        "mode": mode,
        "summary": {
            "total_cases": total,
            "passed_cases": passed_count,
            "overall_pass_rate": rate(passed_count),
            "tool_accuracy": rate(tool_pass_count),
            "argument_accuracy": rate(args_pass_count),
            "grounding_coverage": rate(grounding_pass_count),
        },
        "cases": [result.__dict__ for result in case_results],
    }


def write_json_report(report: dict[str, Any], path: Path = DEFAULT_JSON_OUTPUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_markdown_report(
    report: dict[str, Any],
    path: Path = DEFAULT_MARKDOWN_OUTPUT_PATH,
) -> None:
    summary = report["summary"]
    lines = [
        "# Agent Evaluation Report",
        "",
        f"- Reference date: `{report['reference_date']}` (latest inventory date in SQLite)",
        f"- Mode: `{report['mode']}`",
        f"- Total cases: `{summary['total_cases']}`",
        f"- Overall pass rate: `{summary['overall_pass_rate']:.2%}`",
        f"- Tool accuracy: `{summary['tool_accuracy']:.2%}`",
        f"- Argument accuracy: `{summary['argument_accuracy']:.2%}`",
        f"- Grounding coverage: `{summary['grounding_coverage']:.2%}`",
        "",
        "| Case | Query | Expected Tool | Actual Tool | Tool | Args | Grounding |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            "| {id} | {query} | `{expected}` | `{actual}` | {tool} | {args} | {grounding} |".format(
                id=case["id"],
                query=case["query"],
                expected=case["expected_tool"],
                actual=case["actual_tool"],
                tool="Pass" if case["tool_passed"] else "Fail",
                args="Pass" if case["args_passed"] else "Fail",
                grounding="Pass" if case["grounding_passed"] else "Fail",
            )
        )

    failures = [case for case in report["cases"] if not case["passed"]]
    lines.extend(["", "## Failures", ""])
    if not failures:
        lines.append("No failures.")
    else:
        for case in failures:
            lines.append(f"- `{case['id']}`: missing paths={case['missing_paths']}, error={case['error']}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
