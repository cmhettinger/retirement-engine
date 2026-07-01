"""Current-data chart specs for the retirement summary PDF report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from retirement_engine.projections import AnnualProjectionRow
from retirement_engine.reports.core.renderers.pdf import (
    BarChartSpec,
    ChartPoint,
    ChartSeries,
    GaugeChartSpec,
    LineChartSpec,
    PieChartSpec,
)
from retirement_engine.reports.retirement_summary.pdf.context import RetirementSummaryPdfContext


@dataclass(frozen=True)
class RetirementSummaryChartSet:
    readiness_gauge: GaugeChartSpec
    spending_breakdown: PieChartSpec
    must_pay_vs_optional_spending: PieChartSpec
    income_mix: PieChartSpec
    asset_allocation_by_tax_treatment: PieChartSpec
    net_worth_allocation: BarChartSpec
    portfolio_balance_over_time: LineChartSpec
    income_vs_expenses: LineChartSpec
    annual_surplus_deficit: BarChartSpec
    annual_withdrawals: BarChartSpec
    cumulative_withdrawals: LineChartSpec


def build_retirement_summary_chart_set(
    context: RetirementSummaryPdfContext,
) -> RetirementSummaryChartSet:
    """Build first-generation chart specs from current deterministic report data."""

    projection_rows = _sample_projection_rows(context.annual_projection.rows)
    return RetirementSummaryChartSet(
        readiness_gauge=_readiness_gauge(context),
        spending_breakdown=_spending_breakdown(context),
        must_pay_vs_optional_spending=_must_pay_vs_optional_spending(context),
        income_mix=_income_mix(context),
        asset_allocation_by_tax_treatment=_asset_allocation_by_tax_treatment(context),
        net_worth_allocation=_net_worth_allocation(context),
        portfolio_balance_over_time=_portfolio_balance_over_time(projection_rows),
        income_vs_expenses=_income_vs_expenses(projection_rows),
        annual_surplus_deficit=_annual_surplus_deficit(projection_rows),
        annual_withdrawals=_annual_withdrawals(projection_rows),
        cumulative_withdrawals=_cumulative_withdrawals(projection_rows),
    )


def _readiness_gauge(context: RetirementSummaryPdfContext) -> GaugeChartSpec:
    funded_ratio = context.readiness.funded_ratio or Decimal(0)
    return GaugeChartSpec(
        title="Funded Ratio / Readiness Gauge",
        value=funded_ratio,
        value_label=_percent(funded_ratio),
        target_label="100% funded",
    )


def _spending_breakdown(context: RetirementSummaryPdfContext) -> PieChartSpec:
    totals = _sum_points(
        (row.category or "Unclassified", row.annual_equivalent)
        for row in context.budget_rows
        if row.has_amount
    )
    if context.expense_summary.annual_replacement_reserve > 0:
        totals["Replacement reserves"] = (
            totals.get("Replacement reserves", Decimal(0))
            + context.expense_summary.annual_replacement_reserve
        )
    return PieChartSpec(title="Spending Breakdown", points=_positive_points(totals))


def _must_pay_vs_optional_spending(context: RetirementSummaryPdfContext) -> PieChartSpec:
    return PieChartSpec(
        title="Must-Pay vs Optional Spending",
        points=_positive_points(
            {
                "Must-pay": context.expense_summary.annual_must_pay_spending,
                "Optional": context.expense_summary.annual_optional_spending,
                "Replacement reserves": context.expense_summary.annual_replacement_reserve,
            }
        ),
    )


def _income_mix(context: RetirementSummaryPdfContext) -> PieChartSpec:
    totals = _sum_points(
        (row.source or "Unclassified", row.annual_equivalent)
        for row in context.income_rows
        if row.has_amount
    )
    return PieChartSpec(title="Income Mix", points=_positive_points(totals))


def _asset_allocation_by_tax_treatment(context: RetirementSummaryPdfContext) -> PieChartSpec:
    return PieChartSpec(
        title="Asset Allocation by Tax Treatment",
        points=_positive_points(context.asset_rollup.by_tax_treatment),
    )


def _net_worth_allocation(context: RetirementSummaryPdfContext) -> BarChartSpec:
    return BarChartSpec(
        title="Net Worth Allocation",
        series=(
            ChartSeries(
                "Balance sheet",
                (
                    ChartPoint("Assets", context.expense_summary.total_assets),
                    ChartPoint("Liabilities", -context.expense_summary.total_liabilities),
                    ChartPoint("Net worth", context.expense_summary.net_worth),
                ),
            ),
        ),
        value_axis_label="Dollars",
    )


def _portfolio_balance_over_time(
    rows: tuple[AnnualProjectionRow, ...],
) -> LineChartSpec:
    return LineChartSpec(
        title="Portfolio Balance Over Time",
        series=(
            ChartSeries(
                "Ending portfolio",
                tuple(ChartPoint(str(row.calendar_year), row.ending_portfolio) for row in rows),
            ),
        ),
        value_axis_label="Dollars",
    )


def _income_vs_expenses(rows: tuple[AnnualProjectionRow, ...]) -> LineChartSpec:
    return LineChartSpec(
        title="Income vs Expenses",
        series=(
            ChartSeries(
                "Income",
                tuple(ChartPoint(str(row.calendar_year), row.annual_income) for row in rows),
            ),
            ChartSeries(
                "Expenses",
                tuple(ChartPoint(str(row.calendar_year), row.annual_expenses) for row in rows),
            ),
        ),
        value_axis_label="Dollars",
    )


def _annual_surplus_deficit(rows: tuple[AnnualProjectionRow, ...]) -> BarChartSpec:
    return BarChartSpec(
        title="Annual Surplus / Deficit",
        series=(
            ChartSeries(
                "Income minus expenses",
                tuple(
                    ChartPoint(
                        str(row.calendar_year),
                        row.annual_income - row.annual_expenses,
                    )
                    for row in rows
                ),
            ),
        ),
        value_axis_label="Dollars",
    )


def _annual_withdrawals(rows: tuple[AnnualProjectionRow, ...]) -> BarChartSpec:
    return BarChartSpec(
        title="Annual Withdrawals",
        series=(
            ChartSeries(
                "Withdrawals",
                tuple(ChartPoint(str(row.calendar_year), row.withdrawal) for row in rows),
            ),
        ),
        value_axis_label="Dollars",
    )


def _cumulative_withdrawals(rows: tuple[AnnualProjectionRow, ...]) -> LineChartSpec:
    cumulative = Decimal(0)
    points = []
    for row in rows:
        cumulative += row.withdrawal
        points.append(ChartPoint(str(row.calendar_year), cumulative))
    return LineChartSpec(
        title="Cumulative Withdrawals",
        series=(ChartSeries("Cumulative withdrawals", tuple(points)),),
        value_axis_label="Dollars",
    )


def _sample_projection_rows(
    rows: tuple[AnnualProjectionRow, ...],
    *,
    max_points: int = 12,
) -> tuple[AnnualProjectionRow, ...]:
    if len(rows) <= max_points:
        return rows
    last_index = len(rows) - 1
    selected_indexes = {
        round(index * last_index / (max_points - 1)) for index in range(max_points)
    }
    return tuple(row for index, row in enumerate(rows) if index in selected_indexes)


def _sum_points(items: Iterable[tuple[str, Decimal]]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for label, value in items:
        totals[str(label)] = totals.get(str(label), Decimal(0)) + value
    return totals


def _positive_points(totals: dict[str, Decimal]) -> tuple[ChartPoint, ...]:
    points = tuple(
        ChartPoint(label, value)
        for label, value in sorted(totals.items())
        if value > 0
    )
    if points:
        return points
    return (ChartPoint("No current data", 1),)


def _percent(value: Decimal) -> str:
    return f"{value * Decimal(100):,.1f}%"


__all__ = [
    "RetirementSummaryChartSet",
    "build_retirement_summary_chart_set",
]
