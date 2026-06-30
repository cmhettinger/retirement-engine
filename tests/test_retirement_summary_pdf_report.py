from datetime import datetime
from pathlib import Path

from retirement_engine.config import load_config
from retirement_engine.reports.retirement_summary.pdf import (
    build_retirement_summary_pdf_context,
    render_retirement_summary_pdf,
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
