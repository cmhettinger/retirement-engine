"""Liability rollup calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.workbook.reader import WorkbookCellValue, WorkbookRow


@dataclass(frozen=True)
class NormalizedLiabilityRow:
    row_id: str | None
    owner: str
    liability_type: str
    lender: str
    current_balance: Decimal
    interest_rate: Decimal
    monthly_payment: Decimal
    payoff_year: int | None
    has_balance: bool


@dataclass(frozen=True)
class LiabilityRollup:
    total_liabilities: Decimal
    monthly_debt_payments: Decimal
    annual_debt_payments: Decimal
    net_worth_impact: Decimal
    by_owner: dict[str, Decimal]
    by_liability_type: dict[str, Decimal]
    payoff_years: tuple[int, ...]
    earliest_payoff_year: int | None
    latest_payoff_year: int | None
    item_count: int


def normalize_liability_rows(rows: tuple[WorkbookRow, ...]) -> tuple[NormalizedLiabilityRow, ...]:
    """Normalize liability rows into typed balances, payments, and payoff years."""

    return tuple(normalize_liability_row(row) for row in rows)


def normalize_liability_row(row: WorkbookRow) -> NormalizedLiabilityRow:
    """Normalize one liability row without modifying workbook data."""

    return NormalizedLiabilityRow(
        row_id=row.row_id,
        owner=_text(row.values.get("Owner")),
        liability_type=_text(row.values.get("Liability Type")),
        lender=_text(row.values.get("Lender")),
        current_balance=_money(row.values.get("Current Balance")),
        interest_rate=_money(row.values.get("Interest Rate")),
        monthly_payment=_money(row.values.get("Monthly Payment")),
        payoff_year=_optional_int(row.values.get("Payoff Year")),
        has_balance=_has_entered_value(row.values.get("Current Balance")),
    )


def rollup_liabilities(rows: tuple[NormalizedLiabilityRow, ...]) -> LiabilityRollup:
    total_liabilities = sum((row.current_balance for row in rows), start=Decimal(0))
    monthly_debt_payments = sum((row.monthly_payment for row in rows), start=Decimal(0))
    payoff_years = tuple(sorted({row.payoff_year for row in rows if row.payoff_year is not None}))

    return LiabilityRollup(
        total_liabilities=total_liabilities,
        monthly_debt_payments=monthly_debt_payments,
        annual_debt_payments=monthly_debt_payments * Decimal(12),
        net_worth_impact=-total_liabilities,
        by_owner=_sum_by(rows, key="owner"),
        by_liability_type=_sum_by(rows, key="liability_type"),
        payoff_years=payoff_years,
        earliest_payoff_year=payoff_years[0] if payoff_years else None,
        latest_payoff_year=payoff_years[-1] if payoff_years else None,
        item_count=sum(1 for row in rows if row.has_balance),
    )


def total_liabilities(rows: tuple[NormalizedLiabilityRow, ...]) -> Decimal:
    return rollup_liabilities(rows).total_liabilities


def _sum_by(rows: tuple[NormalizedLiabilityRow, ...], *, key: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        group = str(getattr(row, key))
        if not group:
            group = "Unclassified"
        totals[group] = totals.get(group, Decimal(0)) + row.current_balance
    return totals


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


def _optional_int(value: WorkbookCellValue) -> int | None:
    number = _money(value)
    if number == 0 and not _has_entered_value(value):
        return None
    return int(number)


def _text(value: WorkbookCellValue) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _has_entered_value(value: WorkbookCellValue) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))
