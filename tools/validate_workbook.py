"""Validate a Retirement Engine workbook and write a JSON report."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from retirement_engine.bootstrap import initialize_application
from retirement_engine.workbook import load_retirement_workbook, validate_retirement_workbook


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="env/config.yml", help="Path to application config.")
    parser.add_argument("--workbook", help="Workbook to validate. Defaults to configured workbook.")
    parser.add_argument(
        "--output",
        default="build/workbook-validation.json",
        help="JSON report path.",
    )
    args = parser.parse_args(argv)

    context = initialize_application(args.config)
    workbook_path = (
        Path(args.workbook).expanduser() if args.workbook else context.config.default_workbook
    )
    workbook = load_retirement_workbook(workbook_path)
    report = validate_retirement_workbook(workbook, context.config)

    output_path = Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = context.config.project_root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {output_path}")
    print(f"Validation status: {report.status}")
    return 0 if report.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
