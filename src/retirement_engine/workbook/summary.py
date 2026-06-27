"""Simple workbook summary calculations for CLI output."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from retirement_engine.calculators import (
    calculate_reserve_rows,
    normalize_asset_rows,
    normalize_budget_rows,
    normalize_income_rows,
    normalize_liability_rows,
    rollup_assets,
    rollup_liabilities,
    rollup_reserves,
    total_annual_budget,
    total_annual_income,
    total_retirement_assets,
)
from retirement_engine.workbook.reader import RetirementWorkbook


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
    calculated_reserve_rows = calculate_reserve_rows(reserve_rows)
    reserve_rollup = rollup_reserves(calculated_reserve_rows)
    income_rows = workbook.sheet("Income").rows
    normalized_income_rows = normalize_income_rows(income_rows)
    asset_rows = workbook.sheet("Assets").rows
    normalized_asset_rows = normalize_asset_rows(asset_rows)
    asset_rollup = rollup_assets(normalized_asset_rows)
    liability_rows = workbook.sheet("Liabilities").rows
    normalized_liability_rows = normalize_liability_rows(liability_rows)
    liability_rollup = rollup_liabilities(normalized_liability_rows)

    return WorkbookSummary(
        workbook=workbook.path,
        people=_people(workbook),
        annual_budget_items=sum(1 for row in normalized_budget_rows if row.has_amount),
        reserve_items=reserve_rollup.item_count,
        income_sources=sum(1 for row in normalized_income_rows if row.has_amount),
        assets=asset_rollup.retirement_item_count,
        liabilities=liability_rollup.item_count,
        annual_expenses=_round_currency(total_annual_budget(normalized_budget_rows)),
        annual_replacement_reserve=_round_currency(reserve_rollup.annual_contribution),
        estimated_retirement_income=_round_currency(total_annual_income(normalized_income_rows)),
        current_retirement_assets=_round_currency(total_retirement_assets(normalized_asset_rows)),
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


def _round_currency(value: float | Decimal) -> int:
    return int(round(value))
