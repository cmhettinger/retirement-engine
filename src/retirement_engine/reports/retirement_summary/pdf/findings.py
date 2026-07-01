"""Evidence-backed findings and actions for the retirement summary PDF."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from retirement_engine.reports.retirement_summary.pdf.context import RetirementSummaryPdfContext


@dataclass(frozen=True)
class ExecutiveFinding:
    category: str
    title: str
    summary: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class RecommendedAction:
    title: str
    rationale: str
    evidence: tuple[str, ...]
    expected_benefit: str
    priority: str
    timeframe: str


@dataclass(frozen=True)
class FindingsActionPlan:
    strengths: tuple[ExecutiveFinding, ...]
    risks: tuple[ExecutiveFinding, ...]
    warnings: tuple[ExecutiveFinding, ...]
    actions: tuple[RecommendedAction, ...]


def build_findings_action_plan(context: RetirementSummaryPdfContext) -> FindingsActionPlan:
    """Build current-data findings and recommendations for task 23 pages."""

    strengths = list(_strengths(context))
    risks = list(_risks(context))
    warnings = list(_warnings(context))
    actions = list(_actions(context))

    return FindingsActionPlan(
        strengths=tuple(strengths),
        risks=tuple(risks),
        warnings=tuple(warnings),
        actions=tuple(actions),
    )


def _strengths(context: RetirementSummaryPdfContext) -> tuple[ExecutiveFinding, ...]:
    readiness = context.readiness
    projection = context.annual_projection
    expense_summary = context.expense_summary
    retirement_dates = context.retirement_dates
    findings: list[ExecutiveFinding] = []

    if readiness.surplus_or_shortfall >= 0:
        findings.append(
            ExecutiveFinding(
                category="Strength",
                title="Deterministic readiness is on track",
                summary=(
                    "Projected retirement assets exceed the deterministic assets "
                    "required by the current workbook assumptions."
                ),
                evidence=(
                    f"Funded ratio: {_percent(readiness.funded_ratio)}",
                    "Projected retirement assets: "
                    f"{_currency(readiness.projected_retirement_assets)}",
                    f"Estimated surplus: {_currency(readiness.surplus_or_shortfall)}",
                ),
            )
        )

    if projection.depletion_year is None and projection.rows:
        findings.append(
            ExecutiveFinding(
                category="Strength",
                title="Projection remains funded through the planning horizon",
                summary=(
                    "The deterministic annual projection does not show portfolio "
                    "depletion before the end of the configured horizon."
                ),
                evidence=(
                    f"Planning horizon: {readiness.planning_horizon_years} years",
                    f"Final projection year: {projection.rows[-1].calendar_year}",
                    f"Ending portfolio: {_currency(projection.rows[-1].ending_portfolio)}",
                ),
            )
        )

    if retirement_dates.earliest_viable_retirement_year is not None:
        findings.append(
            ExecutiveFinding(
                category="Strength",
                title="Retirement date flexibility exists",
                summary=(
                    "The date estimator found at least one viable retirement year "
                    "under the current deterministic projection."
                ),
                evidence=(
                    f"Planned retirement year: {retirement_dates.planned_retirement_year}",
                    "Earliest viable retirement year: "
                    f"{retirement_dates.earliest_viable_retirement_year}",
                ),
            )
        )

    if expense_summary.net_worth > 0:
        findings.append(
            ExecutiveFinding(
                category="Strength",
                title="Current balance sheet is positive",
                summary="Current assets exceed liabilities in the workbook snapshot.",
                evidence=(
                    f"Total assets: {_currency(expense_summary.total_assets)}",
                    f"Total liabilities: {_currency(expense_summary.total_liabilities)}",
                    f"Net worth: {_currency(expense_summary.net_worth)}",
                ),
            )
        )

    return tuple(findings)


def _risks(context: RetirementSummaryPdfContext) -> tuple[ExecutiveFinding, ...]:
    readiness = context.readiness
    expense_summary = context.expense_summary
    projection = context.annual_projection
    findings: list[ExecutiveFinding] = []

    if readiness.surplus_or_shortfall < 0:
        findings.append(
            ExecutiveFinding(
                category="Risk",
                title="Deterministic shortfall",
                summary=(
                    "Projected retirement assets are below the deterministic "
                    "requirement implied by current spending, income, and assumptions."
                ),
                evidence=(
                    f"Funded ratio: {_percent(readiness.funded_ratio)}",
                    "Required retirement assets: "
                    f"{_currency(readiness.required_retirement_assets)}",
                    f"Estimated shortfall: {_currency(abs(readiness.surplus_or_shortfall))}",
                ),
            )
        )

    if readiness.annual_withdrawal_need > 0:
        findings.append(
            ExecutiveFinding(
                category="Risk",
                title="Retirement income does not cover projected spending",
                summary=(
                    "Current income sources leave a recurring spending gap that "
                    "must be covered by portfolio withdrawals or spending changes."
                ),
                evidence=(
                    "Annual retirement income: "
                    f"{_currency(expense_summary.annual_retirement_income)}",
                    f"Annual spending need: {_currency(expense_summary.annual_spending_need)}",
                    f"Annual withdrawal need: {_currency(readiness.annual_withdrawal_need)}",
                ),
            )
        )

    if projection.depletion_year is not None:
        findings.append(
            ExecutiveFinding(
                category="Risk",
                title="Projection shows portfolio depletion",
                summary=(
                    "The current annual projection falls below zero before the end "
                    "of the configured planning horizon."
                ),
                evidence=(
                    f"Depletion year: {projection.depletion_year}",
                    f"Planning horizon: {readiness.planning_horizon_years} years",
                ),
            )
        )

    if expense_summary.total_liabilities > 0:
        findings.append(
            ExecutiveFinding(
                category="Risk",
                title="Debt payments remain part of the plan",
                summary=(
                    "Liabilities and scheduled payments reduce flexibility and "
                    "should be reviewed against the retirement timeline."
                ),
                evidence=(
                    f"Total liabilities: {_currency(expense_summary.total_liabilities)}",
                    f"Annual debt payments: {_currency(expense_summary.annual_debt_payments)}",
                    "Latest payoff year: "
                    f"{_optional_year(context.liability_rollup.latest_payoff_year)}",
                ),
            )
        )

    return tuple(findings)


def _warnings(context: RetirementSummaryPdfContext) -> tuple[ExecutiveFinding, ...]:
    findings: list[ExecutiveFinding] = []

    if context.validation_report.failures:
        examples = tuple(failure.message for failure in context.validation_report.failures[:3])
        findings.append(
            ExecutiveFinding(
                category="Warning",
                title="Workbook validation failures need resolution",
                summary=(
                    "The workbook failed structural or input validation checks, so "
                    "report conclusions should be treated as provisional."
                ),
                evidence=(
                    f"Validation failures: {len(context.validation_report.failures)}",
                    *examples,
                ),
            )
        )

    if context.expense_summary.insurance_review_gap_count > 0:
        findings.append(
            ExecutiveFinding(
                category="Warning",
                title="Insurance records have review gaps",
                summary=(
                    "One or more policy rows are missing provider, premium, "
                    "coverage, or beneficiary fields."
                ),
                evidence=(
                    "Policies needing review: "
                    f"{context.expense_summary.insurance_review_gap_count}",
                    f"Policy count: {context.expense_summary.insurance_policy_count}",
                ),
            )
        )

    if context.expense_summary.annual_replacement_reserve > 0:
        findings.append(
            ExecutiveFinding(
                category="Warning",
                title="Replacement reserves are material",
                summary=(
                    "The workbook includes recurring reserve needs that should be "
                    "funded intentionally rather than treated as surprise expenses."
                ),
                evidence=(
                    f"Reserve items: {context.reserve_rollup.item_count}",
                    "Annual replacement reserve: "
                    f"{_currency(context.expense_summary.annual_replacement_reserve)}",
                ),
            )
        )

    if not findings:
        findings.append(
            ExecutiveFinding(
                category="Warning",
                title="No immediate deterministic warnings",
                summary=(
                    "Current validation and deterministic summary checks did not "
                    "identify a blocking warning."
                ),
                evidence=("Validation status: passed",),
            )
        )

    return tuple(findings)


def _actions(context: RetirementSummaryPdfContext) -> tuple[RecommendedAction, ...]:
    actions: list[RecommendedAction] = [
        RecommendedAction(
            title="Review workbook assumptions before relying on the report",
            rationale=(
                "The report is only as reliable as the assumptions and workbook "
                "inputs driving the deterministic model."
            ),
            evidence=(
                f"Workbook version: {context.workbook_version}",
                f"Validation status: {context.validation_report.status}",
            ),
            expected_benefit="Improves confidence in every downstream planning conclusion.",
            priority="High",
            timeframe="Before using this report for decisions",
        )
    ]

    if context.validation_report.failures:
        actions.append(
            RecommendedAction(
                title="Resolve workbook validation failures",
                rationale=(
                    "Validation failures indicate missing or invalid workbook structure or inputs."
                ),
                evidence=(f"Validation failures: {len(context.validation_report.failures)}",),
                expected_benefit="Prevents known input defects from distorting the report.",
                priority="High",
                timeframe="Immediate",
            )
        )

    if context.readiness.surplus_or_shortfall < 0:
        actions.append(
            RecommendedAction(
                title="Close the deterministic retirement shortfall",
                rationale=(
                    "The current deterministic estimate does not fully fund the "
                    "planned retirement path."
                ),
                evidence=(
                    "Estimated shortfall: "
                    f"{_currency(abs(context.readiness.surplus_or_shortfall))}",
                    f"Funded ratio: {_percent(context.readiness.funded_ratio)}",
                ),
                expected_benefit="Moves the plan toward a fully funded deterministic baseline.",
                priority="High",
                timeframe="0-3 months",
            )
        )
    else:
        actions.append(
            RecommendedAction(
                title="Stress-test the on-track result when simulations are available",
                rationale=(
                    "The current result is deterministic and does not yet include "
                    "Monte Carlo or sequence-of-returns analysis."
                ),
                evidence=(
                    f"Estimated surplus: {_currency(context.readiness.surplus_or_shortfall)}",
                    f"Funded ratio: {_percent(context.readiness.funded_ratio)}",
                ),
                expected_benefit=(
                    "Tests whether the apparent safety margin survives market and "
                    "inflation uncertainty."
                ),
                priority="Medium",
                timeframe="After Monte Carlo tasks are complete",
            )
        )

    if context.readiness.annual_withdrawal_need > 0:
        actions.append(
            RecommendedAction(
                title="Review income gap and withdrawal dependency",
                rationale=(
                    "Projected retirement income does not fully cover spending, so "
                    "the portfolio must supply the gap."
                ),
                evidence=(
                    "Annual income gap: "
                    f"{_currency(abs(context.expense_summary.annual_income_gap))}",
                    "Annual withdrawal need: "
                    f"{_currency(context.readiness.annual_withdrawal_need)}",
                ),
                expected_benefit=(
                    "Clarifies whether spending changes, added income, or planned "
                    "withdrawals are the right response."
                ),
                priority="High",
                timeframe="0-3 months",
            )
        )

    if context.expense_summary.insurance_review_gap_count > 0:
        actions.append(
            RecommendedAction(
                title="Complete insurance policy fields or mark gaps intentional",
                rationale=(
                    "Missing policy fields limit the usefulness of the insurance "
                    "review summary."
                ),
                evidence=(
                    "Policies needing review: "
                    f"{context.expense_summary.insurance_review_gap_count}",
                ),
                expected_benefit="Improves risk-review completeness in the household plan.",
                priority="Medium",
                timeframe="30 days",
            )
        )

    if context.expense_summary.total_liabilities > 0:
        actions.append(
            RecommendedAction(
                title="Compare debt payoff years with the retirement timeline",
                rationale=(
                    "Debt payments can materially affect retirement cash flow and "
                    "flexibility."
                ),
                evidence=(
                    "Annual debt payments: "
                    f"{_currency(context.expense_summary.annual_debt_payments)}",
                    "Latest payoff year: "
                    f"{_optional_year(context.liability_rollup.latest_payoff_year)}",
                ),
                expected_benefit=(
                    "Identifies whether payoff timing should be accelerated before "
                    "or during retirement."
                ),
                priority="Medium",
                timeframe="0-6 months",
            )
        )

    if context.expense_summary.annual_replacement_reserve > 0:
        actions.append(
            RecommendedAction(
                title="Fund replacement reserves as a recurring cash-flow item",
                rationale=(
                    "Reserve needs are already included in spending, but they still "
                    "need a practical funding process."
                ),
                evidence=(
                    "Annual replacement reserve: "
                    f"{_currency(context.expense_summary.annual_replacement_reserve)}",
                    f"Reserve items: {context.reserve_rollup.item_count}",
                ),
                expected_benefit=(
                    "Reduces the chance that predictable replacements become "
                    "unplanned portfolio withdrawals."
                ),
                priority="Medium",
                timeframe="0-6 months",
            )
        )

    if context.retirement_dates.earliest_viable_retirement_year is not None:
        actions.append(
            RecommendedAction(
                title="Compare planned retirement year with viable alternatives",
                rationale=(
                    "The date estimator can help quantify the trade-off between "
                    "retiring as planned and earlier viable dates."
                ),
                evidence=(
                    f"Planned retirement year: {context.retirement_dates.planned_retirement_year}",
                    "Earliest viable retirement year: "
                    f"{context.retirement_dates.earliest_viable_retirement_year}",
                ),
                expected_benefit=(
                    "Turns retirement timing into a visible planning choice rather "
                    "than a fixed assumption."
                ),
                priority="Low",
                timeframe="Annual planning review",
            )
        )
    else:
        actions.append(
            RecommendedAction(
                title="Model later retirement dates or plan changes",
                rationale="No viable retirement year was found in the deterministic date scan.",
                evidence=(
                    f"Planned retirement year: {context.retirement_dates.planned_retirement_year}",
                    "Earliest viable retirement year: n/a",
                ),
                expected_benefit="Finds a timeline that avoids projected depletion.",
                priority="High",
                timeframe="0-3 months",
            )
        )

    return tuple(actions)


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


__all__ = [
    "ExecutiveFinding",
    "FindingsActionPlan",
    "RecommendedAction",
    "build_findings_action_plan",
]
