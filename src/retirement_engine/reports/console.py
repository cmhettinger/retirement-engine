"""Plain-text console summary report."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from retirement_engine.analysis import (
    HouseholdExpenseSummary,
    RetirementReadinessEstimate,
    estimate_retirement_readiness,
    summarize_household_expenses,
)
from retirement_engine.projections import (
    RetirementDateEstimate,
    estimate_retirement_dates,
)
from retirement_engine.workbook.reader import RetirementWorkbook
from retirement_engine.workbook.summary import summarize_retirement_workbook


def render_console_summary_report(workbook: RetirementWorkbook) -> str:
    """Render a plain-text retirement summary report suitable for CLI output."""

    workbook_summary = summarize_retirement_workbook(workbook)
    expense_summary = summarize_household_expenses(workbook)
    readiness = estimate_retirement_readiness(workbook)
    retirement_dates = estimate_retirement_dates(workbook)
    warnings = _warnings(expense_summary, readiness)
    next_steps = _next_steps(expense_summary, readiness, retirement_dates)

    lines = [
        "Retirement Summary Report",
        "=========================",
        "",
        f"Workbook: {_relative_or_absolute(workbook.path)}",
        "People:",
    ]
    lines.extend(f"  {person}" for person in workbook_summary.people)
    lines.extend(
        [
            "",
            "Snapshot",
            "--------",
            f"Annual spending need:        {_currency(expense_summary.annual_spending_need)}",
            f"Monthly spending need:       {_currency(expense_summary.monthly_spending_need)}",
            f"Must-pay annual spending:    {_currency(expense_summary.annual_must_pay_spending)}",
            f"Optional annual spending:    {_currency(expense_summary.annual_optional_spending)}",
            f"Replacement reserve:         {_currency(expense_summary.annual_replacement_reserve)}",
            f"Estimated income:            {_currency(expense_summary.annual_retirement_income)}",
            f"Annual withdrawal need:      {_currency(readiness.annual_withdrawal_need)}",
            "",
            "Balance Sheet",
            "-------------",
            f"Retirement assets:           {_currency(expense_summary.retirement_assets)}",
            f"Total assets:                {_currency(expense_summary.total_assets)}",
            f"Total liabilities:           {_currency(expense_summary.total_liabilities)}",
            f"Net worth:                   {_currency(expense_summary.net_worth)}",
            "",
            "Readiness",
            "---------",
            f"Status:                      {readiness.status.replace('_', ' ')}",
            f"Planned retirement year:     {retirement_dates.planned_retirement_year}",
            "Earliest viable year:        "
            f"{_optional_year(retirement_dates.earliest_viable_retirement_year)}",
            f"Projected retirement assets: {_currency(readiness.projected_retirement_assets)}",
            f"Required retirement assets:  {_currency(readiness.required_retirement_assets)}",
            f"Surplus / shortfall:         {_currency(readiness.surplus_or_shortfall)}",
            f"Funded ratio:                {_percent(readiness.funded_ratio)}",
            "",
            "Insurance",
            "---------",
            f"Annual premiums:             {_currency(expense_summary.annual_insurance_premiums)}",
            f"Coverage amount:             {_currency(expense_summary.insurance_coverage_amount)}",
            f"Policies needing review:     {expense_summary.insurance_review_gap_count}",
            "",
            "Warnings",
            "--------",
        ]
    )
    lines.extend(f"- {warning}" for warning in warnings)
    lines.extend(
        [
            "",
            "Next Steps",
            "----------",
        ]
    )
    lines.extend(f"- {next_step}" for next_step in next_steps)
    return "\n".join(lines) + "\n"


def _warnings(
    expense_summary: HouseholdExpenseSummary,
    readiness: RetirementReadinessEstimate,
) -> tuple[str, ...]:
    warnings = []
    if readiness.status == "shortfall":
        warnings.append(
            "Projected retirement assets are below the required deterministic estimate."
        )
    if readiness.annual_withdrawal_need > 0:
        warnings.append(
            "Estimated retirement income is below projected spending need before "
            "portfolio withdrawals."
        )
    if expense_summary.insurance_review_gap_count > 0:
        warnings.append(
            f"{expense_summary.insurance_review_gap_count} insurance policies have missing fields."
        )
    if not warnings:
        warnings.append("No immediate deterministic warnings were identified.")
    return tuple(warnings)


def _next_steps(
    expense_summary: HouseholdExpenseSummary,
    readiness: RetirementReadinessEstimate,
    retirement_dates: RetirementDateEstimate,
) -> tuple[str, ...]:
    next_steps = [
        "Review workbook assumptions before treating this as planning advice.",
        "Compare must-pay and optional spending for adjustment opportunities.",
    ]
    if readiness.status == "shortfall":
        next_steps.append("Model higher contributions, lower expenses, or a later retirement date.")
    else:
        next_steps.append("Stress-test the on-track result with future Monte Carlo scenarios.")
    if retirement_dates.earliest_viable_retirement_year is not None:
        next_steps.append(
            "Use the retirement date estimate to compare the planned year against earlier options."
        )
    if expense_summary.insurance_review_gap_count > 0:
        next_steps.append("Fill in or intentionally clear insurance policies flagged for review.")
    return tuple(next_steps)


def _currency(value: Decimal) -> str:
    rounded = value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"${rounded:,.0f}"


def _percent(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * Decimal(100):,.1f}%"


def _optional_year(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
