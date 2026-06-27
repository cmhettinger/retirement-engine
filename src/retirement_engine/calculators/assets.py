"""Asset rollup calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.workbook.reader import WorkbookCellValue, WorkbookRow

TAX_TREATMENT_BUCKETS = {
    "Pre-tax": "pre_tax",
    "Roth": "roth",
    "Taxable": "taxable",
    "Cash": "cash",
    "HSA": "hsa",
    "Real Estate": "real_estate",
}
RETIREMENT_ASSET_BUCKETS = frozenset({"pre_tax", "roth", "taxable", "hsa"})


@dataclass(frozen=True)
class NormalizedAssetRow:
    row_id: str | None
    owner: str
    account_type: str
    institution: str
    current_balance: Decimal
    annual_contribution: Decimal
    employer_match: Decimal
    tax_treatment: str
    tax_bucket: str
    has_balance: bool


@dataclass(frozen=True)
class AssetRollup:
    total_assets: Decimal
    retirement_assets: Decimal
    by_owner: dict[str, Decimal]
    by_account_type: dict[str, Decimal]
    by_tax_treatment: dict[str, Decimal]
    by_tax_bucket: dict[str, Decimal]
    item_count: int
    retirement_item_count: int


def normalize_asset_rows(rows: tuple[WorkbookRow, ...]) -> tuple[NormalizedAssetRow, ...]:
    """Normalize asset rows into typed balances and grouping keys."""

    return tuple(normalize_asset_row(row) for row in rows)


def normalize_asset_row(row: WorkbookRow) -> NormalizedAssetRow:
    """Normalize one asset row without modifying workbook data."""

    tax_treatment = _text(row.values.get("Tax Treatment"))
    return NormalizedAssetRow(
        row_id=row.row_id,
        owner=_text(row.values.get("Owner")),
        account_type=_text(row.values.get("Account Type")),
        institution=_text(row.values.get("Institution")),
        current_balance=_money(row.values.get("Current Balance")),
        annual_contribution=_money(row.values.get("Annual Contribution")),
        employer_match=_money(row.values.get("Employer Match")),
        tax_treatment=tax_treatment,
        tax_bucket=_tax_bucket(tax_treatment),
        has_balance=_has_entered_value(row.values.get("Current Balance")),
    )


def rollup_assets(rows: tuple[NormalizedAssetRow, ...]) -> AssetRollup:
    by_owner = _sum_by(rows, key="owner")
    by_account_type = _sum_by(rows, key="account_type")
    by_tax_treatment = _sum_by(rows, key="tax_treatment")
    by_tax_bucket = _sum_by(rows, key="tax_bucket")
    total_assets = sum((row.current_balance for row in rows), start=Decimal(0))
    retirement_rows = tuple(row for row in rows if row.tax_bucket in RETIREMENT_ASSET_BUCKETS)
    retirement_assets = sum(
        (row.current_balance for row in retirement_rows),
        start=Decimal(0),
    )

    return AssetRollup(
        total_assets=total_assets,
        retirement_assets=retirement_assets,
        by_owner=by_owner,
        by_account_type=by_account_type,
        by_tax_treatment=by_tax_treatment,
        by_tax_bucket=by_tax_bucket,
        item_count=sum(1 for row in rows if row.has_balance),
        retirement_item_count=sum(1 for row in retirement_rows if row.has_balance),
    )


def total_retirement_assets(rows: tuple[NormalizedAssetRow, ...]) -> Decimal:
    return rollup_assets(rows).retirement_assets


def _sum_by(rows: tuple[NormalizedAssetRow, ...], *, key: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        group = str(getattr(row, key))
        if not group:
            group = "Unclassified"
        totals[group] = totals.get(group, Decimal(0)) + row.current_balance
    return totals


def _tax_bucket(tax_treatment: str) -> str:
    if tax_treatment in TAX_TREATMENT_BUCKETS:
        return TAX_TREATMENT_BUCKETS[tax_treatment]
    if not tax_treatment:
        return "unclassified"
    return _slug(tax_treatment)


def _slug(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


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


def _text(value: WorkbookCellValue) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _has_entered_value(value: WorkbookCellValue) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))
