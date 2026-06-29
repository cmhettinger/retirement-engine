import json
from pathlib import Path

import pytest

from retirement_engine.cli import main
from retirement_engine.config import load_config


def test_cli_validate_prints_text(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["validate"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Workbook: resources/workbooks/example.xlsx" in output
    assert "Status: passed" in output


def test_cli_validate_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "validation.json"

    exit_code = main(["validate", "--format", "json", "--output", str(output_path)])

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["failures"] == []


def test_cli_summary_prints_text(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["summary"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "People:\n  Han Solo\n  Leia Organa" in output
    assert "Annual Budget Items:          75" in output
    assert "Annual Expenses:\n$183,666" in output
    assert "Current Retirement Assets:\n$1,706,000" in output


def test_cli_summary_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "summary.json"
    config = load_config()

    exit_code = main(
        [
            "--config",
            str(config.source_path),
            "summarize",
            str(config.default_workbook),
            "--format",
            "json",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["people"] == ["Han Solo", "Leia Organa"]
    assert report["counts"]["assets"] == 9
    assert report["totals"]["current_retirement_assets"] == 1706000


def test_cli_report_prints_text(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["report"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Retirement Summary Report" in output
    assert "Annual spending need:        $238,931" in output
    assert "Status:                      on track" in output
    assert "Next Steps\n----------" in output


def test_cli_report_writes_text(tmp_path: Path) -> None:
    output_path = tmp_path / "console-report.txt"

    exit_code = main(["report", "--output", str(output_path)])

    assert exit_code == 0
    report = output_path.read_text(encoding="utf-8")
    assert "Retirement Summary Report" in report
    assert "Earliest viable year:        2026" in report


def test_cli_report_writes_pdf(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output_path = tmp_path / "retirement-summary.pdf"

    exit_code = main(["report", "--format", "pdf", "--output", str(output_path)])

    assert exit_code == 0
    assert output_path.read_bytes().startswith(b"%PDF")
    assert str(output_path) in capsys.readouterr().out
