from decimal import Decimal

from retirement_engine.calculators import (
    normalize_liability_row,
    normalize_liability_rows,
    rollup_liabilities,
    total_liabilities,
)
from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook
from retirement_engine.workbook.reader import WorkbookRow


def test_normalize_liability_row() -> None:
    row = liability_row(
        row_id="liability.test.mortgage",
        owner="Household",
        liability_type="Mortgage",
        lender="Example Bank",
        balance=250000,
        interest_rate="0.045",
        monthly_payment=1800,
        payoff_year=2042,
    )

    normalized = normalize_liability_row(row)

    assert normalized.row_id == "liability.test.mortgage"
    assert normalized.owner == "Household"
    assert normalized.liability_type == "Mortgage"
    assert normalized.lender == "Example Bank"
    assert normalized.current_balance == Decimal(250000)
    assert normalized.interest_rate == Decimal("0.045")
    assert normalized.monthly_payment == Decimal(1800)
    assert normalized.payoff_year == 2042
    assert normalized.has_balance is True


def test_rollup_liabilities_groups_debt_and_payoff_years() -> None:
    rows = normalize_liability_rows(
        (
            liability_row(
                row_id="liability.test.mortgage",
                owner="Household",
                liability_type="Mortgage",
                lender="Bank",
                balance=200000,
                interest_rate="0.04",
                monthly_payment=1500,
                payoff_year=2042,
            ),
            liability_row(
                row_id="liability.test.vehicle",
                owner="Person 1",
                liability_type="Vehicle Loan",
                lender="Auto Lender",
                balance=18000,
                interest_rate="0.05",
                monthly_payment=475,
                payoff_year=2029,
            ),
            liability_row(
                row_id="liability.test.blank",
                owner="Household",
                liability_type="Other Liability",
                lender="",
                balance=None,
                interest_rate=None,
                monthly_payment=None,
                payoff_year=None,
            ),
        )
    )

    rollup = rollup_liabilities(rows)

    assert rollup.item_count == 2
    assert rollup.total_liabilities == Decimal(218000)
    assert rollup.monthly_debt_payments == Decimal(1975)
    assert rollup.annual_debt_payments == Decimal(23700)
    assert rollup.net_worth_impact == Decimal(-218000)
    assert rollup.payoff_years == (2029, 2042)
    assert rollup.earliest_payoff_year == 2029
    assert rollup.latest_payoff_year == 2042
    assert rollup.by_owner == {
        "Household": Decimal(200000),
        "Person 1": Decimal(18000),
    }
    assert rollup.by_liability_type == {
        "Mortgage": Decimal(200000),
        "Vehicle Loan": Decimal(18000),
        "Other Liability": Decimal(0),
    }


def test_rollup_example_liabilities() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    normalized_rows = normalize_liability_rows(workbook.sheet("Liabilities").rows)
    rollup = rollup_liabilities(normalized_rows)

    assert rollup.item_count == 4
    assert total_liabilities(normalized_rows) == Decimal(261300)
    assert rollup.monthly_debt_payments == Decimal(2750)
    assert rollup.annual_debt_payments == Decimal(33000)
    assert rollup.net_worth_impact == Decimal(-261300)
    assert rollup.payoff_years == (2027, 2029, 2042)
    assert rollup.earliest_payoff_year == 2027
    assert rollup.latest_payoff_year == 2042
    assert rollup.by_owner == {"Household": Decimal(261300)}
    assert rollup.by_liability_type == {
        "Mortgage": Decimal(238000),
        "Home Equity Loan": Decimal(0),
        "Vehicle Loan": Decimal(18000),
        "Credit Card Debt": Decimal(3200),
        "Personal Loan": Decimal(0),
        "Student Loan": Decimal(0),
        "Medical Debt": Decimal(0),
        "Other Liability": Decimal(2100),
    }


def liability_row(
    *,
    row_id: str,
    owner: str,
    liability_type: str,
    lender: str,
    balance: int | None,
    interest_rate: str | None,
    monthly_payment: int | None,
    payoff_year: int | None,
) -> WorkbookRow:
    return WorkbookRow(
        row_number=2,
        values={
            "Owner": owner,
            "Liability Type": liability_type,
            "Lender": lender,
            "Current Balance": balance,
            "Interest Rate": interest_rate,
            "Monthly Payment": monthly_payment,
            "Payoff Year": payoff_year,
            "Notes": None,
            "ID": row_id,
        },
    )
