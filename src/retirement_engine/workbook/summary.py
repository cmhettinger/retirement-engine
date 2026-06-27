"""Simple workbook summary calculations for CLI output."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from retirement_engine.calculators import (
    normalize_budget_rows,
    normalize_income_rows,
    total_annual_budget,
    total_annual_income,
)
from retirement_engine.workbook.reader import RetirementWorkbook, WorkbookCellValue, WorkbookRow

RETIREMENT_ASSET_TAX_TREATMENTS = frozenset({"Pre-tax", "Roth", "HSA", "Taxable"})


@dataclass(frozen=True)
class WorkbookSummary:
    workbook: Path
    people: tuple[str, ...]
    annual_budget_items: int
    reserve_items: int
    income_sources: int
    assets: int
    liabilities: int
    annual_expenses: int
    annual_replacement_reserve: int
    estimated_retirement_income: int
    current_retirement_assets: int

    def to_dict(self) -> dict[str, object]:
        return {
            "workbook": str(self.workbook),
            "people": list(self.people),
            "counts": {
                "annual_budget_items": self.annual_budget_items,
                "reserve_items": self.reserve_items,
                "income_sources": self.income_sources,
                "assets": self.assets,
                "liabilities": self.liabilities,
            },
            "totals": {
                "annual_expenses": self.annual_expenses,
                "annual_replacement_reserve": self.annual_replacement_reserve,
                "estimated_retirement_income": self.estimated_retirement_income,
                "current_retirement_assets": self.current_retirement_assets,
            },
        }


def summarize_retirement_workbook(workbook: RetirementWorkbook) -> WorkbookSummary:
    """Build a first-pass summary from workbook rows without mutating the workbook."""

    budget_rows = workbook.sheet("Budget").rows
    normalized_budget_rows = normalize_budget_rows(budget_rows)
    reserve_rows = workbook.sheet("Reserves").rows
    income_rows = workbook.sheet("Income").rows
    normalized_income_rows = normalize_income_rows(income_rows)
    asset_rows = workbook.sheet("Assets").rows
    liability_rows = workbook.sheet("Liabilities").rows
    retirement_asset_rows = tuple(
        row
        for row in asset_rows
        if row.values.get("Tax Treatment") in RETIREMENT_ASSET_TAX_TREATMENTS
        and _has_entered_value(row.values.get("Current Balance"))
    )

    return WorkbookSummary(
        workbook=workbook.path,
        people=_people(workbook),
        annual_budget_items=sum(1 for row in normalized_budget_rows if row.has_amount),
        reserve_items=sum(
            1
            for row in reserve_rows
            if _has_entered_value(row.values.get("Estimated Replacement Cost"))
        ),
        income_sources=sum(1 for row in normalized_income_rows if row.has_amount),
        assets=len(retirement_asset_rows),
        liabilities=sum(
            1 for row in liability_rows if _has_entered_value(row.values.get("Current Balance"))
        ),
        annual_expenses=_round_currency(total_annual_budget(normalized_budget_rows)),
        annual_replacement_reserve=_round_currency(
            sum(_annual_reserve_amount(row) for row in reserve_rows)
        ),
        estimated_retirement_income=_round_currency(total_annual_income(normalized_income_rows)),
        current_retirement_assets=_round_currency(
            sum(_number(row.values.get("Current Balance")) for row in retirement_asset_rows)
        ),
    )


def _people(workbook: RetirementWorkbook) -> tuple[str, ...]:
    assumptions = workbook.sheet("Assumptions")
    names = []
    for row_id in ("assumptions.person1.name", "assumptions.person2.name"):
        row = assumptions.rows_by_id.get(row_id)
        if row is None:
            continue
        value = row.values.get("Value")
        if isinstance(value, str) and value.strip():
            names.append(value.strip())
    return tuple(names)


def _annual_amount(row: WorkbookRow) -> float:
    return _number(row.values.get("Annual")) + (_number(row.values.get("Monthly")) * 12)


def _annual_reserve_amount(row: WorkbookRow) -> float:
    replacement_cost = _number(row.values.get("Estimated Replacement Cost"))
    remaining_life = _number(row.values.get("Remaining Useful Life"))
    if replacement_cost <= 0 or remaining_life <= 0:
        return 0.0
    return replacement_cost / remaining_life


def _has_any_entered_value(row: WorkbookRow, columns: tuple[str, ...]) -> bool:
    return any(_has_entered_value(row.values.get(column)) for column in columns)


def _has_entered_value(value: WorkbookCellValue) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _number(value: WorkbookCellValue) -> float:
    if isinstance(value, bool) or value is None:
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value.strip():
        return float(value)
    return 0.0


def _round_currency(value: float | Decimal) -> int:
    return int(round(value))
