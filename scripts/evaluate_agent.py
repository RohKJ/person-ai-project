from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agent.evaluation import (
    DEFAULT_CASES_PATH,
    DEFAULT_JSON_OUTPUT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    evaluate_cases,
    infer_reference_date,
    load_eval_cases,
    write_json_report,
    write_markdown_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Agent tool routing and grounded outputs.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--mode", choices=["mock", "auto", "openai"], default="mock")
    parser.add_argument("--reference-date", type=str, default=None)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    parser.add_argument("--min-pass-rate", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference_date = (
        datetime.strptime(args.reference_date, "%Y-%m-%d").date()
        if args.reference_date
        else infer_reference_date()
    )
    report = evaluate_cases(
        load_eval_cases(args.cases),
        mode=args.mode,
        reference_date=reference_date,
    )
    write_json_report(report, args.json_output)
    write_markdown_report(report, args.markdown_output)

    summary = report["summary"]
    print(
        "Agent eval: "
        f"{summary['passed_cases']}/{summary['total_cases']} passed, "
        f"tool_accuracy={summary['tool_accuracy']:.2%}, "
        f"argument_accuracy={summary['argument_accuracy']:.2%}, "
        f"grounding_coverage={summary['grounding_coverage']:.2%}"
    )
    print(f"JSON report: {args.json_output}")
    print(f"Markdown report: {args.markdown_output}")

    return 0 if summary["overall_pass_rate"] >= args.min_pass_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())
