from decimal import Decimal

from retirement_engine.calculators import (
    normalize_income_row,
    normalize_income_rows,
    rollup_income,
    total_annual_income,
)
from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook
from retirement_engine.workbook.reader import WorkbookRow


def test_normalize_income_row_with_annual_amount() -> None:
    row = income_row(row_id="income.test.annual", taxable="Yes", annual=12000)

    normalized = normalize_income_row(row)

    assert normalized.annual == Decimal(12000)
    assert normalized.monthly == Decimal(0)
    assert normalized.annual_equivalent == Decimal(12000)
    assert normalized.monthly_equivalent == Decimal(1000)
    assert normalized.taxable == "Yes"
    assert normalized.has_amount is True


def test_normalize_income_row_with_monthly_amount() -> None:
    row = income_row(row_id="income.test.monthly", taxable="No", monthly=250)

    normalized = normalize_income_row(row)

    assert normalized.annual == Decimal(0)
    assert normalized.monthly == Decimal(250)
    assert normalized.annual_equivalent == Decimal(3000)
    assert normalized.monthly_equivalent == Decimal(250)
    assert normalized.taxable == "No"
    assert normalized.has_amount is True


def test_normalize_income_row_with_annual_and_monthly_amounts() -> None:
    row = income_row(row_id="income.test.both", taxable="Yes", annual=600, monthly=50)

    normalized = normalize_income_row(row)

    assert normalized.annual_equivalent == Decimal(1200)
    assert normalized.monthly_equivalent == Decimal(100)


def test_normalize_income_row_without_amounts() -> None:
    row = income_row(row_id="income.test.blank", taxable=None)

    normalized = normalize_income_row(row)

    assert normalized.annual_equivalent == Decimal(0)
    assert normalized.monthly_equivalent == Decimal(0)
    assert normalized.taxable is None
    assert normalized.has_amount is False


def test_rollup_income_by_taxability() -> None:
    rows = normalize_income_rows(
        (
            income_row(row_id="income.test.taxable", taxable="Yes", annual=1200),
            income_row(row_id="income.test.nontaxable", taxable="No", monthly=100),
            income_row(row_id="income.test.unclassified", taxable=None, annual=600),
        )
    )

    rollup = rollup_income(rows)

    assert rollup.total_annual == Decimal(3000)
    assert rollup.taxable_annual == Decimal(1200)
    assert rollup.nontaxable_annual == Decimal(1200)
    assert rollup.unclassified_annual == Decimal(600)
    assert rollup.total_monthly == Decimal(250)
    assert rollup.taxable_monthly == Decimal(100)
    assert rollup.nontaxable_monthly == Decimal(100)
    assert rollup.unclassified_monthly == Decimal(50)


def test_normalize_example_income_total_and_rollups() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    normalized_rows = normalize_income_rows(workbook.sheet("Income").rows)
    rollup = rollup_income(normalized_rows)

    assert sum(1 for row in normalized_rows if row.has_amount) == 11
    assert total_annual_income(normalized_rows) == Decimal(194100)
    assert rollup.taxable_annual == Decimal(182100)
    assert rollup.nontaxable_annual == Decimal(12000)
    assert rollup.unclassified_annual == Decimal(0)


def income_row(
    *,
    row_id: str,
    taxable: str | None,
    annual: int | None = None,
    monthly: int | None = None,
) -> WorkbookRow:
    return WorkbookRow(
        row_number=2,
        values={
            "Owner": "Household",
            "Income Source": "Example",
            "Annual": annual,
            "Monthly": monthly,
            "Taxable": taxable,
            "Notes": None,
            "ID": row_id,
        },
    )
