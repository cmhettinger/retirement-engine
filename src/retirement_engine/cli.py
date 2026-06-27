"""Command-line interface for Retirement Engine."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from retirement_engine.bootstrap import initialize_application
from retirement_engine.config import DEFAULT_CONFIG_PATH
from retirement_engine.workbook import (
    WorkbookValidationReport,
    load_retirement_workbook,
    validate_retirement_workbook,
)
from retirement_engine.workbook.summary import WorkbookSummary, summarize_retirement_workbook


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    context = initialize_application(args.config, log_level=args.log_level)
    workbook_path = _workbook_path(args.workbook, context.config.default_workbook)

    if args.command == "validate":
        workbook = load_retirement_workbook(workbook_path)
        report = validate_retirement_workbook(workbook, context.config)
        _emit_output(_format_validation_report(report, args.output_format), args.output)
        return 0 if report.status == "passed" else 1

    if args.command in {"summary", "summarize"}:
        workbook = load_retirement_workbook(workbook_path)
        summary = summarize_retirement_workbook(workbook)
        _emit_output(_format_summary(summary, args.output_format), args.output)
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="retirement-engine")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to application config.")
    parser.add_argument("--log-level", default="INFO", help="Logging level to use during startup.")
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser("validate", help="Validate a workbook.")
    _add_workbook_argument(validate_parser)
    _add_output_arguments(validate_parser)

    summary_parser = subparsers.add_parser(
        "summary",
        aliases=["summarize"],
        help="Print a workbook summary.",
    )
    _add_workbook_argument(summary_parser)
    _add_output_arguments(summary_parser)

    return parser


def _add_workbook_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "workbook",
        nargs="?",
        help="Workbook to process. Defaults to configured workbook.",
    )


def _add_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
        help="Output format.",
    )
    parser.add_argument("--output", help="Write output to a file instead of stdout.")


def _workbook_path(workbook: str | None, default_workbook: Path) -> Path:
    return Path(workbook).expanduser() if workbook else default_workbook


def _format_validation_report(report: WorkbookValidationReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report.to_dict(), indent=2) + "\n"

    lines = [f"Workbook: {_relative_or_absolute(report.workbook)}", f"Status: {report.status}"]
    if report.failures:
        lines.append("")
        lines.append("Failures:")
        for failure in report.failures:
            location = _failure_location(failure.sheet, failure.row_number, failure.column)
            lines.append(f"  - {failure.message} ({failure.code}{location})")
    return "\n".join(lines) + "\n"


def _format_summary(summary: WorkbookSummary, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(summary.to_dict(), indent=2) + "\n"

    lines = [
        f"Workbook: {_relative_or_absolute(summary.workbook)}",
        "",
        "People:",
    ]
    lines.extend(f"  {person}" for person in summary.people)
    lines.extend(
        [
            "",
            f"Annual Budget Items:      {summary.annual_budget_items:>6}",
            f"Reserve Items:            {summary.reserve_items:>6}",
            f"Income Sources:           {summary.income_sources:>6}",
            f"Assets:                   {summary.assets:>6}",
            f"Liabilities:              {summary.liabilities:>6}",
            "",
            "Annual Expenses:",
            _currency(summary.annual_expenses),
            "",
            "Annual Replacement Reserve:",
            _currency(summary.annual_replacement_reserve),
            "",
            "Estimated Retirement Income:",
            _currency(summary.estimated_retirement_income),
            "",
            "Current Retirement Assets:",
            _currency(summary.current_retirement_assets),
        ]
    )
    return "\n".join(lines) + "\n"


def _emit_output(text: str, output_path: str | None) -> None:
    if output_path is None:
        print(text, end="")
        return

    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _failure_location(sheet: str | None, row_number: int | None, column: str | None) -> str:
    details = []
    if sheet is not None:
        details.append(f"sheet={sheet}")
    if row_number is not None:
        details.append(f"row={row_number}")
    if column is not None:
        details.append(f"column={column}")
    if not details:
        return ""
    return "; " + ", ".join(details)


def _currency(value: int) -> str:
    return f"${value:,.0f}"


if __name__ == "__main__":
    raise SystemExit(main())
