"""Simple deterministic retirement readiness estimates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.analysis.expense_summary import summarize_household_expenses
from retirement_engine.calculators import normalize_asset_rows
from retirement_engine.workbook.reader import RetirementWorkbook, WorkbookCellValue, WorkbookRow

RETIREMENT_ASSET_BUCKETS = frozenset({"pre_tax", "roth", "taxable", "hsa"})


@dataclass(frozen=True)
class RetirementReadinessEstimate:
    status: str
    years_until_retirement: int
    planning_horizon_years: int
    expected_investment_return: Decimal
    inflation_rate: Decimal
    real_return_rate: Decimal
    current_retirement_assets: Decimal
    annual_retirement_contributions: Decimal
    projected_retirement_assets: Decimal
    annual_spending_need: Decimal
    annual_retirement_income: Decimal
    annual_withdrawal_need: Decimal
    required_retirement_assets: Decimal
    desired_cash_reserve: Decimal
    desired_estate_value: Decimal
    surplus_or_shortfall: Decimal
    funded_ratio: Decimal | None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "timeline": {
                "years_until_retirement": self.years_until_retirement,
                "planning_horizon_years": self.planning_horizon_years,
            },
            "assumptions": {
                "expected_investment_return": self.expected_investment_return,
                "inflation_rate": self.inflation_rate,
                "real_return_rate": self.real_return_rate,
            },
            "assets": {
                "current_retirement_assets": self.current_retirement_assets,
                "annual_retirement_contributions": self.annual_retirement_contributions,
                "projected_retirement_assets": self.projected_retirement_assets,
                "required_retirement_assets": self.required_retirement_assets,
                "desired_cash_reserve": self.desired_cash_reserve,
                "desired_estate_value": self.desired_estate_value,
                "surplus_or_shortfall": self.surplus_or_shortfall,
                "funded_ratio": self.funded_ratio,
            },
            "cash_flow": {
                "annual_spending_need": self.annual_spending_need,
                "annual_retirement_income": self.annual_retirement_income,
                "annual_withdrawal_need": self.annual_withdrawal_need,
            },
        }


def estimate_retirement_readiness(workbook: RetirementWorkbook) -> RetirementReadinessEstimate:
    """Estimate retirement readiness using current-dollar deterministic assumptions."""

    assumptions = workbook.sheet("Assumptions").rows_by_id
    household_summary = summarize_household_expenses(workbook)
    asset_rows = normalize_asset_rows(workbook.sheet("Assets").rows)

    years_until_retirement = _years_until_retirement(assumptions)
    planning_horizon_years = int(
        _assumption_decimal(assumptions, "assumptions.household.planning_horizon_years")
    )
    expected_investment_return = _assumption_decimal(
        assumptions,
        "assumptions.household.expected_investment_return",
    )
    inflation_rate = _assumption_decimal(assumptions, "assumptions.household.inflation_rate")
    real_return_rate = _real_return_rate(expected_investment_return, inflation_rate)
    desired_cash_reserve = _assumption_decimal(
        assumptions,
        "assumptions.household.desired_cash_reserve",
    )
    desired_estate_value = _assumption_decimal(
        assumptions,
        "assumptions.household.desired_estate_value",
    )
    annual_retirement_contributions = sum(
        (
            row.annual_contribution + row.employer_match
            for row in asset_rows
            if row.tax_bucket in RETIREMENT_ASSET_BUCKETS
        ),
        start=Decimal(0),
    )
    projected_retirement_assets = _future_value(
        current_value=household_summary.retirement_assets,
        annual_contribution=annual_retirement_contributions,
        annual_return=expected_investment_return,
        years=years_until_retirement,
    )
    annual_withdrawal_need = max(
        household_summary.annual_spending_need - household_summary.annual_retirement_income,
        Decimal(0),
    )
    required_retirement_assets = (
        _present_value_annuity(
            annual_amount=annual_withdrawal_need,
            discount_rate=real_return_rate,
            years=planning_horizon_years,
        )
        + desired_cash_reserve
        + desired_estate_value
    )
    surplus_or_shortfall = projected_retirement_assets - required_retirement_assets

    return RetirementReadinessEstimate(
        status="on_track" if surplus_or_shortfall >= 0 else "shortfall",
        years_until_retirement=years_until_retirement,
        planning_horizon_years=planning_horizon_years,
        expected_investment_return=expected_investment_return,
        inflation_rate=inflation_rate,
        real_return_rate=real_return_rate,
        current_retirement_assets=household_summary.retirement_assets,
        annual_retirement_contributions=annual_retirement_contributions,
        projected_retirement_assets=projected_retirement_assets,
        annual_spending_need=household_summary.annual_spending_need,
        annual_retirement_income=household_summary.annual_retirement_income,
        annual_withdrawal_need=annual_withdrawal_need,
        required_retirement_assets=required_retirement_assets,
        desired_cash_reserve=desired_cash_reserve,
        desired_estate_value=desired_estate_value,
        surplus_or_shortfall=surplus_or_shortfall,
        funded_ratio=(
            projected_retirement_assets / required_retirement_assets
            if required_retirement_assets > 0
            else None
        ),
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
    row = assumptions[row_id]
    return _number(row.values.get("Value"))


def _future_value(
    *,
    current_value: Decimal,
    annual_contribution: Decimal,
    annual_return: Decimal,
    years: int,
) -> Decimal:
    if years <= 0:
        return current_value
    growth = (Decimal(1) + annual_return) ** years
    if annual_return == 0:
        return current_value + (annual_contribution * Decimal(years))
    return current_value * growth + annual_contribution * ((growth - Decimal(1)) / annual_return)


def _present_value_annuity(
    *,
    annual_amount: Decimal,
    discount_rate: Decimal,
    years: int,
) -> Decimal:
    if annual_amount <= 0 or years <= 0:
        return Decimal(0)
    if discount_rate == 0:
        return annual_amount * Decimal(years)
    return annual_amount * (Decimal(1) - (Decimal(1) + discount_rate) ** -years) / discount_rate


def _real_return_rate(expected_investment_return: Decimal, inflation_rate: Decimal) -> Decimal:
    return (Decimal(1) + expected_investment_return) / (Decimal(1) + inflation_rate) - Decimal(1)


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
