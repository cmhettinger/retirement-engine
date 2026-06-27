from decimal import Decimal

from retirement_engine.calculators import (
    normalize_insurance_row,
    normalize_insurance_rows,
    rollup_insurance,
    total_annual_insurance_premiums,
)
from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook
from retirement_engine.workbook.reader import WorkbookRow


def test_normalize_insurance_row() -> None:
    row = insurance_row(
        row_id="insurance.test.life",
        owner="Person 1",
        policy_type="Life Insurance",
        provider="Example Mutual",
        annual_premium=780,
        coverage_amount=250000,
        beneficiary="Person 2",
    )

    normalized = normalize_insurance_row(row)

    assert normalized.row_id == "insurance.test.life"
    assert normalized.owner == "Person 1"
    assert normalized.policy_type == "Life Insurance"
    assert normalized.provider == "Example Mutual"
    assert normalized.annual_premium == Decimal(780)
    assert normalized.coverage_amount == Decimal(250000)
    assert normalized.beneficiary == "Person 2"
    assert normalized.has_policy is True
    assert normalized.missing_fields == ()


def test_rollup_insurance_summarizes_policies_and_gaps() -> None:
    rows = normalize_insurance_rows(
        (
            insurance_row(
                row_id="insurance.test.life",
                owner="Person 1",
                policy_type="Life Insurance",
                provider="Example Mutual",
                annual_premium=780,
                coverage_amount=250000,
                beneficiary="Person 2",
            ),
            insurance_row(
                row_id="insurance.test.health",
                owner="Household",
                policy_type="Health Insurance",
                provider="Example Health",
                annual_premium=7800,
                coverage_amount=0,
                beneficiary="Household",
            ),
            insurance_row(
                row_id="insurance.test.disability",
                owner="Person 1",
                policy_type="Disability Insurance",
                provider=None,
                annual_premium=None,
                coverage_amount=None,
                beneficiary=None,
            ),
        )
    )

    rollup = rollup_insurance(rows)

    assert rollup.policy_count == 2
    assert rollup.review_gap_count == 1
    assert rollup.total_annual_premiums == Decimal(8580)
    assert rollup.monthly_premium_equivalent == Decimal(715)
    assert rollup.total_coverage_amount == Decimal(250000)
    assert rollup.by_owner_premiums == {
        "Person 1": Decimal(780),
        "Household": Decimal(7800),
    }
    assert rollup.by_owner_coverage == {
        "Person 1": Decimal(250000),
        "Household": Decimal(0),
    }
    assert rollup.by_policy_type_premiums == {
        "Life Insurance": Decimal(780),
        "Health Insurance": Decimal(7800),
        "Disability Insurance": Decimal(0),
    }
    assert rollup.policies_needing_review[0].row_id == "insurance.test.disability"
    assert rollup.policies_needing_review[0].missing_fields == (
        "Provider",
        "Annual Premium",
        "Coverage Amount",
        "Beneficiary",
    )


def test_rollup_example_insurance() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    normalized_rows = normalize_insurance_rows(workbook.sheet("Insurance").rows)
    rollup = rollup_insurance(normalized_rows)

    assert rollup.policy_count == 10
    assert rollup.review_gap_count == 2
    assert total_annual_insurance_premiums(normalized_rows) == Decimal(18980)
    assert rollup.monthly_premium_equivalent == Decimal("1581.666666666666666666666667")
    assert rollup.total_coverage_amount == Decimal(2652300)
    assert rollup.by_owner_premiums == {
        "Person 1": Decimal(2880),
        "Person 2": Decimal(3020),
        "Household": Decimal(13080),
    }
    assert rollup.by_owner_coverage == {
        "Person 1": Decimal(415000),
        "Person 2": Decimal(415000),
        "Household": Decimal(1822300),
    }
    assert rollup.by_policy_type_premiums == {
        "Life Insurance": Decimal(1500),
        "Disability Insurance": Decimal(0),
        "Long-Term Care Insurance": Decimal(4400),
        "Health Insurance": Decimal(7800),
        "Dental Insurance": Decimal(660),
        "Vision Insurance": Decimal(300),
        "Homeowners Insurance": Decimal(1800),
        "Auto Insurance": Decimal(2100),
        "Umbrella Insurance": Decimal(420),
    }
    assert [row.row_id for row in rollup.policies_needing_review] == [
        "insurance.person1.disability_insurance",
        "insurance.person2.disability_insurance",
    ]


def insurance_row(
    *,
    row_id: str,
    owner: str,
    policy_type: str,
    provider: str | None,
    annual_premium: int | None,
    coverage_amount: int | None,
    beneficiary: str | None,
) -> WorkbookRow:
    return WorkbookRow(
        row_number=2,
        values={
            "Owner": owner,
            "Policy Type": policy_type,
            "Provider": provider,
            "Annual Premium": annual_premium,
            "Coverage Amount": coverage_amount,
            "Beneficiary": beneficiary,
            "Notes": None,
            "ID": row_id,
        },
    )
