"""Income normalization calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.workbook.reader import WorkbookCellValue, WorkbookRow


@dataclass(frozen=True)
class NormalizedIncomeRow:
    row_id: str | None
    owner: str
    source: str
    taxable: str | None
    annual: Decimal
    monthly: Decimal
    annual_equivalent: Decimal
    monthly_equivalent: Decimal
    has_amount: bool


@dataclass(frozen=True)
class IncomeRollup:
    total_annual: Decimal
    taxable_annual: Decimal
    nontaxable_annual: Decimal
    unclassified_annual: Decimal
    total_monthly: Decimal
    taxable_monthly: Decimal
    nontaxable_monthly: Decimal
    unclassified_monthly: Decimal


def normalize_income_rows(rows: tuple[WorkbookRow, ...]) -> tuple[NormalizedIncomeRow, ...]:
    """Normalize income rows into annual and monthly equivalents."""

    return tuple(normalize_income_row(row) for row in rows)


def normalize_income_row(row: WorkbookRow) -> NormalizedIncomeRow:
    """Normalize one income row without modifying workbook data."""

    annual = _money(row.values.get("Annual"))
    monthly = _money(row.values.get("Monthly"))
    annual_equivalent = annual + (monthly * Decimal(12))

    return NormalizedIncomeRow(
        row_id=row.row_id,
        owner=_text(row.values.get("Owner")),
        source=_text(row.values.get("Income Source")),
        taxable=_optional_text(row.values.get("Taxable")),
        annual=annual,
        monthly=monthly,
        annual_equivalent=annual_equivalent,
        monthly_equivalent=annual_equivalent / Decimal(12),
        has_amount=_has_entered_value(row.values.get("Annual"))
        or _has_entered_value(row.values.get("Monthly")),
    )


def rollup_income(rows: tuple[NormalizedIncomeRow, ...]) -> IncomeRollup:
    total_annual = sum((row.annual_equivalent for row in rows), start=Decimal(0))
    taxable_annual = sum(
        (row.annual_equivalent for row in rows if row.taxable == "Yes"),
        start=Decimal(0),
    )
    nontaxable_annual = sum(
        (row.annual_equivalent for row in rows if row.taxable == "No"),
        start=Decimal(0),
    )
    unclassified_annual = sum(
        (row.annual_equivalent for row in rows if row.taxable not in {"Yes", "No"}),
        start=Decimal(0),
    )

    return IncomeRollup(
        total_annual=total_annual,
        taxable_annual=taxable_annual,
        nontaxable_annual=nontaxable_annual,
        unclassified_annual=unclassified_annual,
        total_monthly=total_annual / Decimal(12),
        taxable_monthly=taxable_annual / Decimal(12),
        nontaxable_monthly=nontaxable_annual / Decimal(12),
        unclassified_monthly=unclassified_annual / Decimal(12),
    )


def total_annual_income(rows: tuple[NormalizedIncomeRow, ...]) -> Decimal:
    return rollup_income(rows).total_annual


def _money(value: WorkbookCellValue) -> Decimal:
    if isinstance(value, bool) or value is None:
        return Decimal(0)
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str) and value.strip():
        return Decimal(value.strip())
    return Decimal(0)


def _text(value: WorkbookCellValue) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_text(value: WorkbookCellValue) -> str | None:
    text = _text(value)
    return text or None


def _has_entered_value(value: WorkbookCellValue) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))
