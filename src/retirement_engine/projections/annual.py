"""Simple year-by-year retirement projection engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from retirement_engine.analysis.expense_summary import summarize_household_expenses
from retirement_engine.calculators import normalize_asset_rows
from retirement_engine.workbook.reader import RetirementWorkbook, WorkbookCellValue, WorkbookRow

RETIREMENT_ASSET_BUCKETS = frozenset({"pre_tax", "roth", "taxable", "hsa"})


@dataclass(frozen=True)
class AnnualProjectionRow:
    year_index: int
    calendar_year: int
    person1_age: int
    person2_age: int
    is_retirement_year: bool
    is_retired: bool
    starting_portfolio: Decimal
    contributions: Decimal
    investment_return: Decimal
    annual_expenses: Decimal
    annual_income: Decimal
    withdrawal: Decimal
    ending_portfolio: Decimal

    def to_dict(self) -> dict[str, object]:
        return {
            "year_index": self.year_index,
            "calendar_year": self.calendar_year,
            "person1_age": self.person1_age,
            "person2_age": self.person2_age,
            "is_retirement_year": self.is_retirement_year,
            "is_retired": self.is_retired,
            "starting_portfolio": self.starting_portfolio,
            "contributions": self.contributions,
            "investment_return": self.investment_return,
            "annual_expenses": self.annual_expenses,
            "annual_income": self.annual_income,
            "withdrawal": self.withdrawal,
            "ending_portfolio": self.ending_portfolio,
        }


@dataclass(frozen=True)
class AnnualProjection:
    start_year: int
    retirement_year: int
    years_until_retirement: int
    planning_horizon_years: int
    expected_investment_return: Decimal
    inflation_rate: Decimal
    current_retirement_assets: Decimal
    annual_retirement_contributions: Decimal
    rows: tuple[AnnualProjectionRow, ...]
    depletion_year: int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "start_year": self.start_year,
            "retirement_year": self.retirement_year,
            "years_until_retirement": self.years_until_retirement,
            "planning_horizon_years": self.planning_horizon_years,
            "expected_investment_return": self.expected_investment_return,
            "inflation_rate": self.inflation_rate,
            "current_retirement_assets": self.current_retirement_assets,
            "annual_retirement_contributions": self.annual_retirement_contributions,
            "depletion_year": self.depletion_year,
            "rows": [row.to_dict() for row in self.rows],
        }


def project_retirement_years(
    workbook: RetirementWorkbook,
    *,
    start_year: int | None = None,
) -> AnnualProjection:
    """Project annual portfolio balances through the configured planning horizon."""

    assumptions = workbook.sheet("Assumptions").rows_by_id
    household_summary = summarize_household_expenses(workbook)
    asset_rows = normalize_asset_rows(workbook.sheet("Assets").rows)

    projection_start_year = start_year if start_year is not None else date.today().year
    person1_current_age = int(_assumption_decimal(assumptions, "assumptions.person1.current_age"))
    person2_current_age = int(_assumption_decimal(assumptions, "assumptions.person2.current_age"))
    years_until_retirement = _years_until_retirement(assumptions)
    planning_horizon_years = int(
        _assumption_decimal(assumptions, "assumptions.household.planning_horizon_years")
    )
    expected_investment_return = _assumption_decimal(
        assumptions,
        "assumptions.household.expected_investment_return",
    )
    inflation_rate = _assumption_decimal(assumptions, "assumptions.household.inflation_rate")
    annual_retirement_contributions = sum(
        (
            row.annual_contribution + row.employer_match
            for row in asset_rows
            if row.tax_bucket in RETIREMENT_ASSET_BUCKETS
        ),
        start=Decimal(0),
    )

    rows = []
    depletion_year = None
    starting_portfolio = household_summary.retirement_assets
    for year_index in range(1, planning_horizon_years + 1):
        is_retirement_year = year_index == years_until_retirement
        is_retired = year_index > years_until_retirement
        inflation_factor = (Decimal(1) + inflation_rate) ** year_index
        annual_expenses = household_summary.annual_spending_need * inflation_factor
        annual_income = household_summary.annual_retirement_income * inflation_factor
        contributions = Decimal(0) if is_retired else annual_retirement_contributions
        investment_return = starting_portfolio * expected_investment_return
        withdrawal = max(annual_expenses - annual_income, Decimal(0)) if is_retired else Decimal(0)
        ending_portfolio = starting_portfolio + investment_return + contributions - withdrawal
        calendar_year = projection_start_year + year_index

        row = AnnualProjectionRow(
            year_index=year_index,
            calendar_year=calendar_year,
            person1_age=person1_current_age + year_index,
            person2_age=person2_current_age + year_index,
            is_retirement_year=is_retirement_year,
            is_retired=is_retired,
            starting_portfolio=starting_portfolio,
            contributions=contributions,
            investment_return=investment_return,
            annual_expenses=annual_expenses,
            annual_income=annual_income,
            withdrawal=withdrawal,
            ending_portfolio=ending_portfolio,
        )
        rows.append(row)

        if depletion_year is None and ending_portfolio < 0:
            depletion_year = calendar_year
        starting_portfolio = ending_portfolio

    return AnnualProjection(
        start_year=projection_start_year,
        retirement_year=projection_start_year + years_until_retirement,
        years_until_retirement=years_until_retirement,
        planning_horizon_years=planning_horizon_years,
        expected_investment_return=expected_investment_return,
        inflation_rate=inflation_rate,
        current_retirement_assets=household_summary.retirement_assets,
        annual_retirement_contributions=annual_retirement_contributions,
        rows=tuple(rows),
        depletion_year=depletion_year,
    )


def _years_until_retirement(assumptions: Mapping[str, WorkbookRow]) -> int:
    years = []
    for person in ("person1", "person2"):
        current_age = _assumption_decimal(assumptions, f"assumptions.{person}.current_age")
        retirement_age = _assumption_decimal(
            assumptions,
            f"assumptions.{person}.planned_retirement_age",
        )
        years.append(max(int(retirement_age - current_age), 0))
    return min(years)


def _assumption_decimal(assumptions: Mapping[str, WorkbookRow], row_id: str) -> Decimal:
    return _number(assumptions[row_id].values.get("Value"))


def _number(value: WorkbookCellValue) -> Decimal:
    if isinstance(value, bool) or value is None:
        return Decimal(0)
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str) and value.strip():
        return Decimal(value.strip())
    return Decimal(0)
