from decimal import Decimal

from retirement_engine.analysis import summarize_household_expenses
from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook


def test_summarize_household_expenses_combines_workbook_calculators() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    summary = summarize_household_expenses(workbook)

    assert summary.annual_budget_spending == Decimal(183666)
    assert summary.monthly_budget_spending == Decimal("15305.5")
    assert summary.annual_must_pay_spending == Decimal(134470)
    assert summary.monthly_must_pay_spending == Decimal("11205.83333333333333333333333")
    assert summary.annual_optional_spending == Decimal(49196)
    assert summary.monthly_optional_spending == Decimal("4099.666666666666666666666667")
    assert summary.annual_replacement_reserve == Decimal("55265.14430014430014430014431")
    assert summary.monthly_replacement_reserve == Decimal("4605.428691678691678691678692")
    assert summary.annual_spending_need == Decimal("238931.1443001443001443001443")
    assert summary.monthly_spending_need == Decimal("19910.92869167869167869167869")

    assert summary.annual_retirement_income == Decimal(194100)
    assert summary.monthly_retirement_income == Decimal(16175)
    assert summary.annual_income_gap == Decimal("-44831.1443001443001443001443")

    assert summary.retirement_assets == Decimal(1706000)
    assert summary.total_assets == Decimal(2401000)
    assert summary.total_liabilities == Decimal(261300)
    assert summary.net_worth == Decimal(2139700)
    assert summary.annual_debt_payments == Decimal(33000)
    assert summary.monthly_debt_payments == Decimal(2750)

    assert summary.annual_insurance_premiums == Decimal(18980)
    assert summary.monthly_insurance_premiums == Decimal("1581.666666666666666666666667")
    assert summary.insurance_coverage_amount == Decimal(2652300)
    assert summary.insurance_policy_count == 10
    assert summary.insurance_review_gap_count == 2


def test_household_expense_summary_serializes_to_grouped_dict() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    summary = summarize_household_expenses(workbook)

    assert summary.to_dict()["spending"] == {
        "annual_spending_need": Decimal("238931.1443001443001443001443"),
        "monthly_spending_need": Decimal("19910.92869167869167869167869"),
        "annual_budget_spending": Decimal(183666),
        "monthly_budget_spending": Decimal("15305.5"),
        "annual_must_pay_spending": Decimal(134470),
        "monthly_must_pay_spending": Decimal("11205.83333333333333333333333"),
        "annual_optional_spending": Decimal(49196),
        "monthly_optional_spending": Decimal("4099.666666666666666666666667"),
        "annual_replacement_reserve": Decimal("55265.14430014430014430014431"),
        "monthly_replacement_reserve": Decimal("4605.428691678691678691678692"),
    }
    assert summary.to_dict()["insurance"] == {
        "annual_insurance_premiums": Decimal(18980),
        "monthly_insurance_premiums": Decimal("1581.666666666666666666666667"),
        "insurance_coverage_amount": Decimal(2652300),
        "insurance_policy_count": 10,
        "insurance_review_gap_count": 2,
    }
