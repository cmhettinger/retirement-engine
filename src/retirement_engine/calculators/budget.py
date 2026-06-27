"""Budget normalization calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.workbook.reader import WorkbookCellValue, WorkbookRow


@dataclass(frozen=True)
class NormalizedBudgetRow:
    row_id: str | None
    category: str
    item: str
    must_pay: str | None
    annual: Decimal
    monthly: Decimal
    annual_equivalent: Decimal
    monthly_equivalent: Decimal
    has_amount: bool


def normalize_budget_rows(rows: tuple[WorkbookRow, ...]) -> tuple[NormalizedBudgetRow, ...]:
    """Normalize budget rows into annual and monthly equivalents."""

    return tuple(normalize_budget_row(row) for row in rows)


def normalize_budget_row(row: WorkbookRow) -> NormalizedBudgetRow:
    """Normalize one budget row without modifying workbook data."""

    annual = _money(row.values.get("Annual"))
    monthly = _money(row.values.get("Monthly"))
    annual_equivalent = annual + (monthly * Decimal(12))

    return NormalizedBudgetRow(
        row_id=row.row_id,
        category=_text(row.values.get("Category")),
        item=_text(row.values.get("Item")),
        must_pay=_optional_text(row.values.get("Must Pay")),
        annual=annual,
        monthly=monthly,
        annual_equivalent=annual_equivalent,
        monthly_equivalent=annual_equivalent / Decimal(12),
        has_amount=_has_entered_value(row.values.get("Annual"))
        or _has_entered_value(row.values.get("Monthly")),
    )


def total_annual_budget(rows: tuple[NormalizedBudgetRow, ...]) -> Decimal:
    return sum((row.annual_equivalent for row in rows), start=Decimal(0))


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
