from pathlib import Path

from openpyxl import Workbook

from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook


def test_load_example_workbook_parses_expected_sheets() -> None:
    config = load_config()

    workbook = load_retirement_workbook(config.default_workbook)

    assert workbook.path == config.default_workbook
    assert tuple(workbook.sheets) == (
        "Assumptions",
        "Budget",
        "Reserves",
        "Income",
        "Assets",
        "Liabilities",
        "Insurance",
    )


def test_load_example_workbook_parses_rows_by_header() -> None:
    config = load_config()

    workbook = load_retirement_workbook(config.default_workbook)

    assumptions = workbook.sheet("Assumptions")
    assert assumptions.headers == ("Person / Scope", "Assumption", "Value", "Notes", "ID")
    assert assumptions.rows_by_id["system.workbook.version"].values["Value"] == "0.1.0"
    assert assumptions.rows_by_id["assumptions.person1.name"].values["Value"] == "Han Solo"

    budget = workbook.sheet("Budget")
    mortgage = budget.rows_by_id["budget.housing.mortgage_rent"]
    assert mortgage.row_number == 2
    assert mortgage.values["Category"] == "Housing"
    assert mortgage.values["Monthly"] == 2450
    assert mortgage.values["Annual"] is None


def test_load_workbook_skips_empty_rows(tmp_path: Path) -> None:
    source = tmp_path / "workbook.xlsx"
    openpyxl_workbook = Workbook()
    sheet = openpyxl_workbook.active
    sheet.title = "Example"
    sheet.append(["Name", "Amount", "ID"])
    sheet.append(["First", 10, "row.first"])
    sheet.append([None, None, None])
    sheet.append(["Second", None, "row.second"])
    openpyxl_workbook.save(source)

    workbook = load_retirement_workbook(source)

    example = workbook.sheet("Example")
    assert example.headers == ("Name", "Amount", "ID")
    assert [row.row_number for row in example.rows] == [2, 4]
    assert example.rows_by_id["row.second"].values == {
        "Name": "Second",
        "Amount": None,
        "ID": "row.second",
    }
