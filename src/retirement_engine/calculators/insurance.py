"""Insurance policy summary calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.workbook.reader import WorkbookCellValue, WorkbookRow


@dataclass(frozen=True)
class NormalizedInsuranceRow:
    row_id: str | None
    owner: str
    policy_type: str
    provider: str
    annual_premium: Decimal
    coverage_amount: Decimal
    beneficiary: str
    has_policy: bool
    missing_fields: tuple[str, ...]


@dataclass(frozen=True)
class InsuranceRollup:
    total_annual_premiums: Decimal
    monthly_premium_equivalent: Decimal
    total_coverage_amount: Decimal
    by_owner_premiums: dict[str, Decimal]
    by_owner_coverage: dict[str, Decimal]
    by_policy_type_premiums: dict[str, Decimal]
    by_policy_type_coverage: dict[str, Decimal]
    policies_needing_review: tuple[NormalizedInsuranceRow, ...]
    policy_count: int
    review_gap_count: int


def normalize_insurance_rows(rows: tuple[WorkbookRow, ...]) -> tuple[NormalizedInsuranceRow, ...]:
    """Normalize insurance rows into typed premiums, coverage, and review gaps."""

    return tuple(normalize_insurance_row(row) for row in rows)


def normalize_insurance_row(row: WorkbookRow) -> NormalizedInsuranceRow:
    """Normalize one insurance row without modifying workbook data."""

    has_provider = _has_entered_value(row.values.get("Provider"))
    has_annual_premium = _has_entered_value(row.values.get("Annual Premium"))
    has_coverage_amount = _has_entered_value(row.values.get("Coverage Amount"))
    has_beneficiary = _has_entered_value(row.values.get("Beneficiary"))
    missing_fields = _missing_fields(
        provider=has_provider,
        annual_premium=has_annual_premium,
        coverage_amount=has_coverage_amount,
        beneficiary=has_beneficiary,
    )

    return NormalizedInsuranceRow(
        row_id=row.row_id,
        owner=_text(row.values.get("Owner")),
        policy_type=_text(row.values.get("Policy Type")),
        provider=_text(row.values.get("Provider")),
        annual_premium=_money(row.values.get("Annual Premium")),
        coverage_amount=_money(row.values.get("Coverage Amount")),
        beneficiary=_text(row.values.get("Beneficiary")),
        has_policy=has_provider or has_annual_premium or has_coverage_amount or has_beneficiary,
        missing_fields=missing_fields,
    )


def rollup_insurance(rows: tuple[NormalizedInsuranceRow, ...]) -> InsuranceRollup:
    total_annual_premiums = sum((row.annual_premium for row in rows), start=Decimal(0))
    total_coverage_amount = sum((row.coverage_amount for row in rows), start=Decimal(0))
    policies_needing_review = tuple(row for row in rows if row.missing_fields)

    return InsuranceRollup(
        total_annual_premiums=total_annual_premiums,
        monthly_premium_equivalent=total_annual_premiums / Decimal(12),
        total_coverage_amount=total_coverage_amount,
        by_owner_premiums=_sum_by(rows, key="owner", amount="annual_premium"),
        by_owner_coverage=_sum_by(rows, key="owner", amount="coverage_amount"),
        by_policy_type_premiums=_sum_by(rows, key="policy_type", amount="annual_premium"),
        by_policy_type_coverage=_sum_by(rows, key="policy_type", amount="coverage_amount"),
        policies_needing_review=policies_needing_review,
        policy_count=sum(1 for row in rows if row.has_policy),
        review_gap_count=len(policies_needing_review),
    )


def total_annual_insurance_premiums(rows: tuple[NormalizedInsuranceRow, ...]) -> Decimal:
    return rollup_insurance(rows).total_annual_premiums


def _sum_by(
    rows: tuple[NormalizedInsuranceRow, ...],
    *,
    key: str,
    amount: str,
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        group = str(getattr(row, key))
        if not group:
            group = "Unclassified"
        totals[group] = totals.get(group, Decimal(0)) + getattr(row, amount)
    return totals


def _missing_fields(
    *,
    provider: bool,
    annual_premium: bool,
    coverage_amount: bool,
    beneficiary: bool,
) -> tuple[str, ...]:
    missing = []
    if not provider:
        missing.append("Provider")
    if not annual_premium:
        missing.append("Annual Premium")
    if not coverage_amount:
        missing.append("Coverage Amount")
    if not beneficiary:
        missing.append("Beneficiary")
    return tuple(missing)


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
