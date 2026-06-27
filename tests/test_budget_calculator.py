from decimal import Decimal

from retirement_engine.calculators import (
    normalize_budget_row,
    normalize_budget_rows,
    total_annual_budget,
)
from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook
from retirement_engine.workbook.reader import WorkbookRow


def test_normalize_budget_row_with_annual_amount() -> None:
    row = budget_row(row_id="budget.test.annual", annual=1200)

    normalized = normalize_budget_row(row)

    assert normalized.annual == Decimal(1200)
    assert normalized.monthly == Decimal(0)
    assert normalized.annual_equivalent == Decimal(1200)
    assert normalized.monthly_equivalent == Decimal(100)
    assert normalized.has_amount is True


def test_normalize_budget_row_with_monthly_amount() -> None:
    row = budget_row(row_id="budget.test.monthly", monthly=125)

    normalized = normalize_budget_row(row)

    assert normalized.annual == Decimal(0)
    assert normalized.monthly == Decimal(125)
    assert normalized.annual_equivalent == Decimal(1500)
    assert normalized.monthly_equivalent == Decimal(125)
    assert normalized.has_amount is True


def test_normalize_budget_row_with_annual_and_monthly_amounts() -> None:
    row = budget_row(row_id="budget.test.both", annual=600, monthly=50)

    normalized = normalize_budget_row(row)

    assert normalized.annual_equivalent == Decimal(1200)
    assert normalized.monthly_equivalent == Decimal(100)


def test_normalize_budget_row_without_amounts() -> None:
    row = budget_row(row_id="budget.test.blank")

    normalized = normalize_budget_row(row)

    assert normalized.annual_equivalent == Decimal(0)
    assert normalized.monthly_equivalent == Decimal(0)
    assert normalized.has_amount is False


def test_normalize_example_budget_total() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    normalized_rows = normalize_budget_rows(workbook.sheet("Budget").rows)

    assert sum(1 for row in normalized_rows if row.has_amount) == 75
    assert total_annual_budget(normalized_rows) == Decimal(183666)


def budget_row(
    *,
    row_id: str,
    annual: int | None = None,
    monthly: int | None = None,
) -> WorkbookRow:
    return WorkbookRow(
        row_number=2,
        values={
            "Must Pay": "Yes",
            "Category": "Test",
            "Item": "Example",
            "Annual": annual,
            "Monthly": monthly,
            "Notes": None,
            "ID": row_id,
        },
    )
