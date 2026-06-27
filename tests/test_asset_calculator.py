from decimal import Decimal

from retirement_engine.calculators import (
    normalize_asset_row,
    normalize_asset_rows,
    rollup_assets,
    total_retirement_assets,
)
from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook
from retirement_engine.workbook.reader import WorkbookRow


def test_normalize_asset_row() -> None:
    row = asset_row(
        row_id="asset.test.401k",
        owner="Person 1",
        account_type="401(k)",
        institution="Example 401(k)",
        balance=120000,
        contribution=10000,
        employer_match=5000,
        tax_treatment="Pre-tax",
    )

    normalized = normalize_asset_row(row)

    assert normalized.row_id == "asset.test.401k"
    assert normalized.owner == "Person 1"
    assert normalized.account_type == "401(k)"
    assert normalized.institution == "Example 401(k)"
    assert normalized.current_balance == Decimal(120000)
    assert normalized.annual_contribution == Decimal(10000)
    assert normalized.employer_match == Decimal(5000)
    assert normalized.tax_treatment == "Pre-tax"
    assert normalized.tax_bucket == "pre_tax"
    assert normalized.has_balance is True


def test_rollup_assets_groups_balances() -> None:
    rows = normalize_asset_rows(
        (
            asset_row(
                row_id="asset.test.401k",
                owner="Person 1",
                account_type="401(k)",
                institution="Employer",
                balance=100000,
                contribution=0,
                employer_match=0,
                tax_treatment="Pre-tax",
            ),
            asset_row(
                row_id="asset.test.roth",
                owner="Person 1",
                account_type="Roth IRA",
                institution="Brokerage",
                balance=50000,
                contribution=0,
                employer_match=0,
                tax_treatment="Roth",
            ),
            asset_row(
                row_id="asset.test.cash",
                owner="Household",
                account_type="Cash / Savings",
                institution="Bank",
                balance=25000,
                contribution=0,
                employer_match=0,
                tax_treatment="Cash",
            ),
            asset_row(
                row_id="asset.test.blank",
                owner="Household",
                account_type="Other",
                institution="",
                balance=None,
                contribution=None,
                employer_match=None,
                tax_treatment="",
            ),
        )
    )

    rollup = rollup_assets(rows)

    assert rollup.item_count == 3
    assert rollup.retirement_item_count == 2
    assert rollup.total_assets == Decimal(175000)
    assert rollup.retirement_assets == Decimal(150000)
    assert rollup.by_owner == {
        "Person 1": Decimal(150000),
        "Household": Decimal(25000),
    }
    assert rollup.by_account_type == {
        "401(k)": Decimal(100000),
        "Roth IRA": Decimal(50000),
        "Cash / Savings": Decimal(25000),
        "Other": Decimal(0),
    }
    assert rollup.by_tax_bucket == {
        "pre_tax": Decimal(100000),
        "roth": Decimal(50000),
        "cash": Decimal(25000),
        "unclassified": Decimal(0),
    }


def test_rollup_example_assets() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    normalized_rows = normalize_asset_rows(workbook.sheet("Assets").rows)
    rollup = rollup_assets(normalized_rows)

    assert rollup.item_count == 13
    assert rollup.retirement_item_count == 9
    assert rollup.total_assets == Decimal(2401000)
    assert total_retirement_assets(normalized_rows) == Decimal(1706000)
    assert rollup.by_owner == {
        "Person 1": Decimal(738000),
        "Person 2": Decimal(693000),
        "Household": Decimal(970000),
    }
    assert rollup.by_tax_bucket == {
        "pre_tax": Decimal(1165000),
        "roth": Decimal(202000),
        "hsa": Decimal(64000),
        "taxable": Decimal(275000),
        "cash": Decimal(137000),
        "real_estate": Decimal(520000),
        "personal_property": Decimal(38000),
    }


def asset_row(
    *,
    row_id: str,
    owner: str,
    account_type: str,
    institution: str,
    balance: int | None,
    contribution: int | None,
    employer_match: int | None,
    tax_treatment: str,
) -> WorkbookRow:
    return WorkbookRow(
        row_number=2,
        values={
            "Owner": owner,
            "Account Type": account_type,
            "Institution": institution,
            "Current Balance": balance,
            "Annual Contribution": contribution,
            "Employer Match": employer_match,
            "Tax Treatment": tax_treatment,
            "Notes": None,
            "ID": row_id,
        },
    )
