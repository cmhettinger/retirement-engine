import json
import shutil
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook, validate_retirement_workbook


def test_validate_example_workbook_passes() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    report = validate_retirement_workbook(workbook, config)

    assert report.status == "passed"
    assert report.to_dict() == {
        "status": "passed",
        "workbook": str(config.default_workbook),
        "summary": {"failure_count": 0},
        "failures": [],
    }


def test_validate_workbook_reports_structured_failures(tmp_path: Path) -> None:
    config = load_config()
    broken_workbook = tmp_path / "broken.xlsx"
    shutil.copyfile(config.default_workbook, broken_workbook)

    openpyxl_workbook = load_workbook(broken_workbook)
    budget = openpyxl_workbook["Budget"]
    budget["A2"] = "Maybe"
    budget["G3"] = budget["G2"].value
    budget["G4"] = ""
    assumptions = openpyxl_workbook["Assumptions"]
    assumptions["C2"] = "9.9.9"
    openpyxl_workbook.save(broken_workbook)
    openpyxl_workbook.close()

    workbook = load_retirement_workbook(broken_workbook)
    report = validate_retirement_workbook(workbook, config)

    failure_codes = [failure.code for failure in report.failures]
    assert report.status == "failed"
    assert "workbook_version_mismatch" in failure_codes
    assert "invalid_yes_no" in failure_codes
    assert "duplicate_stable_id" in failure_codes
    assert "missing_stable_id" in failure_codes


def test_validate_workbook_tool_writes_json_report(tmp_path: Path) -> None:
    config = load_config()
    output_path = tmp_path / "validation.json"

    result = subprocess.run(
        [
            sys.executable,
            "tools/validate_workbook.py",
            "--config",
            str(config.source_path),
            "--workbook",
            str(config.default_workbook),
            "--output",
            str(output_path),
        ],
        cwd=config.project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["summary"] == {"failure_count": 0}
    assert report["failures"] == []
