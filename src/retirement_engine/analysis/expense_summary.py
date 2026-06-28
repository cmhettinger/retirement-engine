"""Household retirement expense summary analysis."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.calculators import (
    calculate_reserve_rows,
    normalize_asset_rows,
    normalize_budget_rows,
    normalize_income_rows,
    normalize_insurance_rows,
    normalize_liability_rows,
    rollup_assets,
    rollup_income,
    rollup_insurance,
    rollup_liabilities,
    rollup_reserves,
    total_annual_budget,
)
from retirement_engine.workbook.reader import RetirementWorkbook


@dataclass(frozen=True)
class HouseholdExpenseSummary:
    annual_spending_need: Decimal
    monthly_spending_need: Decimal
    annual_budget_spending: Decimal
    monthly_budget_spending: Decimal
    annual_must_pay_spending: Decimal
    monthly_must_pay_spending: Decimal
    annual_optional_spending: Decimal
    monthly_optional_spending: Decimal
    annual_replacement_reserve: Decimal
    monthly_replacement_reserve: Decimal
    annual_retirement_income: Decimal
    monthly_retirement_income: Decimal
    annual_income_gap: Decimal
    retirement_assets: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    annual_debt_payments: Decimal
    monthly_debt_payments: Decimal
    annual_insurance_premiums: Decimal
    monthly_insurance_premiums: Decimal
    insurance_coverage_amount: Decimal
    insurance_policy_count: int
    insurance_review_gap_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "spending": {
                "annual_spending_need": self.annual_spending_need,
                "monthly_spending_need": self.monthly_spending_need,
                "annual_budget_spending": self.annual_budget_spending,
                "monthly_budget_spending": self.monthly_budget_spending,
                "annual_must_pay_spending": self.annual_must_pay_spending,
                "monthly_must_pay_spending": self.monthly_must_pay_spending,
                "annual_optional_spending": self.annual_optional_spending,
                "monthly_optional_spending": self.monthly_optional_spending,
                "annual_replacement_reserve": self.annual_replacement_reserve,
                "monthly_replacement_reserve": self.monthly_replacement_reserve,
            },
            "income": {
                "annual_retirement_income": self.annual_retirement_income,
                "monthly_retirement_income": self.monthly_retirement_income,
                "annual_income_gap": self.annual_income_gap,
            },
            "balance_sheet": {
                "retirement_assets": self.retirement_assets,
                "total_assets": self.total_assets,
                "total_liabilities": self.total_liabilities,
                "net_worth": self.net_worth,
                "annual_debt_payments": self.annual_debt_payments,
                "monthly_debt_payments": self.monthly_debt_payments,
            },
            "insurance": {
                "annual_insurance_premiums": self.annual_insurance_premiums,
                "monthly_insurance_premiums": self.monthly_insurance_premiums,
                "insurance_coverage_amount": self.insurance_coverage_amount,
                "insurance_policy_count": self.insurance_policy_count,
                "insurance_review_gap_count": self.insurance_review_gap_count,
            },
        }


def summarize_household_expenses(workbook: RetirementWorkbook) -> HouseholdExpenseSummary:
    """Combine workbook calculators into a household retirement expense summary."""

    budget_rows = normalize_budget_rows(workbook.sheet("Budget").rows)
    reserve_rollup = rollup_reserves(calculate_reserve_rows(workbook.sheet("Reserves").rows))
    income_rollup = rollup_income(normalize_income_rows(workbook.sheet("Income").rows))
    asset_rollup = rollup_assets(normalize_asset_rows(workbook.sheet("Assets").rows))
    liability_rollup = rollup_liabilities(
        normalize_liability_rows(workbook.sheet("Liabilities").rows)
    )
    insurance_rollup = rollup_insurance(normalize_insurance_rows(workbook.sheet("Insurance").rows))

    annual_budget_spending = total_annual_budget(budget_rows)
    annual_must_pay_spending = sum(
        (row.annual_equivalent for row in budget_rows if row.must_pay == "Yes"),
        start=Decimal(0),
    )
    annual_optional_spending = annual_budget_spending - annual_must_pay_spending
    annual_spending_need = annual_budget_spending + reserve_rollup.annual_contribution

    return HouseholdExpenseSummary(
        annual_spending_need=annual_spending_need,
        monthly_spending_need=annual_spending_need / Decimal(12),
        annual_budget_spending=annual_budget_spending,
        monthly_budget_spending=annual_budget_spending / Decimal(12),
        annual_must_pay_spending=annual_must_pay_spending,
        monthly_must_pay_spending=annual_must_pay_spending / Decimal(12),
        annual_optional_spending=annual_optional_spending,
        monthly_optional_spending=annual_optional_spending / Decimal(12),
        annual_replacement_reserve=reserve_rollup.annual_contribution,
        monthly_replacement_reserve=reserve_rollup.monthly_contribution,
        annual_retirement_income=income_rollup.total_annual,
        monthly_retirement_income=income_rollup.total_monthly,
        annual_income_gap=income_rollup.total_annual - annual_spending_need,
        retirement_assets=asset_rollup.retirement_assets,
        total_assets=asset_rollup.total_assets,
        total_liabilities=liability_rollup.total_liabilities,
        net_worth=asset_rollup.total_assets - liability_rollup.total_liabilities,
        annual_debt_payments=liability_rollup.annual_debt_payments,
        monthly_debt_payments=liability_rollup.monthly_debt_payments,
        annual_insurance_premiums=insurance_rollup.total_annual_premiums,
        monthly_insurance_premiums=insurance_rollup.monthly_premium_equivalent,
        insurance_coverage_amount=insurance_rollup.total_coverage_amount,
        insurance_policy_count=insurance_rollup.policy_count,
        insurance_review_gap_count=insurance_rollup.review_gap_count,
    )
