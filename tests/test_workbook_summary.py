from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook
from retirement_engine.workbook.summary import summarize_retirement_workbook


def test_summarize_example_workbook() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    summary = summarize_retirement_workbook(workbook)

    assert summary.people == ("Han Solo", "Leia Organa")
    assert summary.annual_budget_items == 75
    assert summary.reserve_items == 22
    assert summary.income_sources == 11
    assert summary.assets == 9
    assert summary.liabilities == 4
    assert summary.annual_expenses == 183666
    assert summary.annual_replacement_reserve == 55265
    assert summary.estimated_retirement_income == 194100
    assert summary.current_retirement_assets == 1706000


def test_workbook_summary_serializes_to_json_ready_dict() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    summary = summarize_retirement_workbook(workbook)

    assert summary.to_dict()["counts"] == {
        "annual_budget_items": 75,
        "reserve_items": 22,
        "income_sources": 11,
        "assets": 9,
        "liabilities": 4,
    }
    assert summary.to_dict()["totals"] == {
        "annual_expenses": 183666,
        "annual_replacement_reserve": 55265,
        "estimated_retirement_income": 194100,
        "current_retirement_assets": 1706000,
    }
