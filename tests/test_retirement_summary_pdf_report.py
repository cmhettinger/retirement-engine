from datetime import datetime
from pathlib import Path

from reportlab.platypus import SimpleDocTemplate

from retirement_engine.config import load_config
from retirement_engine.reports.core.branding import register_brand_fonts
from retirement_engine.reports.core.renderers.pdf import (
    bar_chart,
    gauge_chart,
    line_chart,
    pie_chart,
)
from retirement_engine.reports.retirement_summary.pdf import (
    build_retirement_summary_chart_set,
    build_retirement_summary_pdf_context,
    render_retirement_summary_pdf,
)
from retirement_engine.reports.retirement_summary.pdf.render import (
    _plain_language_assessment,
    _readiness_dashboard_rows,
)
from retirement_engine.workbook import load_retirement_workbook


def test_build_retirement_summary_pdf_context_gathers_report_inputs() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)
    generated_at = datetime(2026, 6, 30, 9, 15)

    context = build_retirement_summary_pdf_context(
        workbook,
        generated_at=generated_at,
        config=config,
    )

    assert context.workbook_summary.people == ("Han Solo", "Leia Organa")
    assert context.workbook_version == config.supported_workbook_version
    assert context.engine_version == config.application_version
    assert context.validation_report.status == "passed"
    assert context.annual_projection.start_year == generated_at.year
    assert len(context.annual_projection.rows) == 35
    assert sum(1 for row in context.budget_rows if row.has_amount) == 75
    assert context.reserve_rollup.annual_contribution == (
        context.expense_summary.annual_replacement_reserve
    )
    assert context.income_rollup.total_annual == context.expense_summary.annual_retirement_income
    assert context.asset_rollup.total_assets == context.expense_summary.total_assets
    assert context.asset_rollup.retirement_assets == context.expense_summary.retirement_assets
    assert context.liability_rollup.total_liabilities == context.expense_summary.total_liabilities
    assert context.liability_rollup.annual_debt_payments == (
        context.expense_summary.annual_debt_payments
    )
    assert context.insurance_rollup.total_annual_premiums == (
        context.expense_summary.annual_insurance_premiums
    )
    assert context.insurance_rollup.review_gap_count == (
        context.expense_summary.insurance_review_gap_count
    )
    assert context.warnings
    assert context.next_steps


def test_build_retirement_summary_chart_set_covers_current_data_charts() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)
    generated_at = datetime(2026, 6, 30, 9, 15)
    context = build_retirement_summary_pdf_context(
        workbook,
        generated_at=generated_at,
        config=config,
    )

    charts = build_retirement_summary_chart_set(context)

    assert charts.readiness_gauge.title == "Funded Ratio / Readiness Gauge"
    assert charts.readiness_gauge.value == context.readiness.funded_ratio
    assert charts.readiness_gauge.maximum == 3
    assert charts.readiness_gauge.maximum_label == "300.0% scale"
    assert charts.spending_breakdown.points
    assert charts.must_pay_vs_optional_spending.points
    assert charts.income_mix.points
    assert charts.asset_allocation_by_tax_treatment.points
    assert charts.net_worth_allocation.series[0].points[0].label == "Assets"
    assert charts.portfolio_balance_over_time.series[0].points[0].label == "2027"
    assert len(charts.portfolio_balance_over_time.series[0].points) <= 12
    assert len(charts.income_vs_expenses.series) == 2
    assert charts.annual_surplus_deficit.series[0].points
    assert charts.annual_withdrawals.series[0].points
    assert charts.cumulative_withdrawals.series[0].points[-1].value > 0


def test_executive_readiness_dashboard_uses_current_deterministic_metrics() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)
    generated_at = datetime(2026, 6, 30, 9, 15)
    context = build_retirement_summary_pdf_context(
        workbook,
        generated_at=generated_at,
        config=config,
    )

    rows = _readiness_dashboard_rows(context)
    labels = [row[0] for row in rows]
    assessment = _plain_language_assessment(context)

    assert labels == [
        "Metric",
        "Deterministic readiness status",
        "Funded ratio",
        "Planned retirement year",
        "Earliest viable retirement year",
        "Planning horizon",
        "Annual retirement income",
        "Annual retirement spending",
        "Projected portfolio assets",
        "Estimated ending estate",
        "Annual withdrawal need",
        "Estimated surplus / shortfall",
    ]
    assert rows[1][1] == "On Track"
    assert rows[2][1].endswith("%")
    assert rows[3][1] == str(context.retirement_dates.planned_retirement_year)
    assert rows[4][1] == str(context.retirement_dates.earliest_viable_retirement_year)
    assert rows[5][1] == f"{context.readiness.planning_horizon_years} years"
    assert "Probability of success" not in labels
    assert "funded ratio" in assessment
    assert str(context.retirement_dates.planned_retirement_year) in assessment


def test_retirement_summary_chart_set_renders_to_pdf(tmp_path: Path) -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)
    generated_at = datetime(2026, 6, 30, 9, 15)
    context = build_retirement_summary_pdf_context(
        workbook,
        generated_at=generated_at,
        config=config,
    )
    charts = build_retirement_summary_chart_set(context)
    theme = register_brand_fonts()
    output_path = tmp_path / "retirement-summary-charts.pdf"

    drawings = [
        gauge_chart(charts.readiness_gauge, theme=theme),
        pie_chart(charts.spending_breakdown, theme=theme),
        pie_chart(charts.must_pay_vs_optional_spending, theme=theme),
        pie_chart(charts.income_mix, theme=theme),
        pie_chart(charts.asset_allocation_by_tax_treatment, theme=theme),
        bar_chart(charts.net_worth_allocation, theme=theme),
        line_chart(charts.portfolio_balance_over_time, theme=theme),
        line_chart(charts.income_vs_expenses, theme=theme),
        bar_chart(charts.annual_surplus_deficit, theme=theme),
        bar_chart(charts.annual_withdrawals, theme=theme),
        line_chart(charts.cumulative_withdrawals, theme=theme),
    ]

    SimpleDocTemplate(str(output_path)).build(drawings)

    assert output_path.read_bytes().startswith(b"%PDF")


def test_render_retirement_summary_pdf_writes_pdf(tmp_path: Path) -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)
    output_path = tmp_path / "retirement-summary.pdf"

    result = render_retirement_summary_pdf(
        workbook,
        output_dir=tmp_path,
        output_path=output_path,
        config=config,
    )

    assert result.primary_artifact.path == output_path
    assert result.primary_artifact.media_type == "application/pdf"
    assert output_path.read_bytes().startswith(b"%PDF")
