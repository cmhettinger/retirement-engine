"""Replacement reserve calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.workbook.reader import WorkbookCellValue, WorkbookRow


@dataclass(frozen=True)
class CalculatedReserveRow:
    row_id: str | None
    item: str
    replacement_cost: Decimal
    expected_useful_life: Decimal
    current_age: Decimal
    remaining_useful_life: Decimal
    next_replacement_year: int | None
    annual_contribution: Decimal
    monthly_contribution: Decimal
    has_amount: bool


@dataclass(frozen=True)
class ReserveRollup:
    item_count: int
    annual_contribution: Decimal
    monthly_contribution: Decimal


def calculate_reserve_rows(rows: tuple[WorkbookRow, ...]) -> tuple[CalculatedReserveRow, ...]:
    """Calculate replacement reserve contributions for workbook reserve rows."""

    return tuple(calculate_reserve_row(row) for row in rows)


def calculate_reserve_row(row: WorkbookRow) -> CalculatedReserveRow:
    """Calculate one reserve row without modifying workbook data."""

    replacement_cost = _money(row.values.get("Estimated Replacement Cost"))
    expected_useful_life = _number(row.values.get("Expected Useful Life"))
    current_age = _number(row.values.get("Current Age"))
    remaining_useful_life = _remaining_useful_life(
        explicit_remaining_life=_number(row.values.get("Remaining Useful Life")),
        expected_useful_life=expected_useful_life,
        current_age=current_age,
    )
    annual_contribution = _annual_contribution(replacement_cost, remaining_useful_life)

    return CalculatedReserveRow(
        row_id=row.row_id,
        item=_text(row.values.get("Reserve Item")),
        replacement_cost=replacement_cost,
        expected_useful_life=expected_useful_life,
        current_age=current_age,
        remaining_useful_life=remaining_useful_life,
        next_replacement_year=_optional_int(row.values.get("Next Replacement Year")),
        annual_contribution=annual_contribution,
        monthly_contribution=annual_contribution / Decimal(12),
        has_amount=_has_entered_value(row.values.get("Estimated Replacement Cost")),
    )


def rollup_reserves(rows: tuple[CalculatedReserveRow, ...]) -> ReserveRollup:
    annual_contribution = sum((row.annual_contribution for row in rows), start=Decimal(0))
    return ReserveRollup(
        item_count=sum(1 for row in rows if row.has_amount),
        annual_contribution=annual_contribution,
        monthly_contribution=annual_contribution / Decimal(12),
    )


def total_annual_reserve_contribution(rows: tuple[CalculatedReserveRow, ...]) -> Decimal:
    return rollup_reserves(rows).annual_contribution


def _remaining_useful_life(
    *,
    explicit_remaining_life: Decimal,
    expected_useful_life: Decimal,
    current_age: Decimal,
) -> Decimal:
    if explicit_remaining_life > 0:
        return explicit_remaining_life

    calculated_remaining_life = expected_useful_life - current_age
    if calculated_remaining_life > 0:
        return calculated_remaining_life

    return Decimal(0)


def _annual_contribution(replacement_cost: Decimal, remaining_useful_life: Decimal) -> Decimal:
    if replacement_cost <= 0 or remaining_useful_life <= 0:
        return Decimal(0)
    return replacement_cost / remaining_useful_life


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


def _number(value: WorkbookCellValue) -> Decimal:
    return _money(value)


def _optional_int(value: WorkbookCellValue) -> int | None:
    number = _number(value)
    if number == 0 and not _has_entered_value(value):
        return None
    return int(number)


def _text(value: WorkbookCellValue) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _has_entered_value(value: WorkbookCellValue) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))
