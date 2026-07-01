"""PDF renderer for the retirement summary report."""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from reportlab.platypus import PageBreak, Paragraph, Table, TableStyle

from retirement_engine.analysis import HouseholdExpenseSummary
from retirement_engine.config import AppConfig
from retirement_engine.reports.core.contracts import RenderContext, RenderResult, ReportMetadata
from retirement_engine.reports.core.renderers.pdf import (
    HeaderFooterSpec,
    PdfRenderer,
    gauge_chart,
    navigable_heading,
    paragraph,
    professional_letter_title_page,
    section_divider,
    spacer,
    table_of_contents,
)
from retirement_engine.reports.core.renderers.pdf.tables import simple_table
from retirement_engine.reports.retirement_summary.pdf.charts import (
    build_retirement_summary_chart_set,
)
from retirement_engine.reports.retirement_summary.pdf.context import (
    RetirementSummaryPdfContext,
    build_retirement_summary_pdf_context,
)
from retirement_engine.workbook.reader import RetirementWorkbook

REPORT_ID = "retirement.summary"
TITLE = "Retirement Summary"
SUBTITLE = "Household Retirement Readiness"
HEADER_TEXT = "RETIREMENT ENGINE"
FOOTER_TEXT = "CONFIDENTIAL FINANCIAL INFORMATION"


def render_retirement_summary_pdf(
    workbook: RetirementWorkbook,
    *,
    output_dir: str | Path,
    output_path: str | Path | None = None,
    generated_at: datetime | None = None,
    config: AppConfig | None = None,
) -> RenderResult:
    """Render a printable PDF version of the retirement summary report."""

    generated_at = generated_at or datetime.now().astimezone()
    report_context = build_retirement_summary_pdf_context(
        workbook,
        generated_at=generated_at,
        config=config,
    )
    metadata = ReportMetadata(
        report_id=REPORT_ID,
        title=TITLE,
        subtitle=SUBTITLE,
        as_of=generated_at.date(),
        generated_at=generated_at,
        tags=("retirement", "summary", "task-15"),
    )
    renderer = PdfRenderer(
        metadata=metadata,
        context=RenderContext(output_dir=Path(output_dir)),
    )
    story: list[Any] = [
        *professional_letter_title_page(
            title=metadata.title,
            subtitle=metadata.subtitle or "",
            report_date=metadata.as_of,
            header_text=HEADER_TEXT,
            footer_text=FOOTER_TEXT,
            classification_text=FOOTER_TEXT,
            branding=renderer.branding,
            theme=renderer.theme,
            prepared_for_name=_household_name(report_context.workbook_summary.people),
        ),
        PageBreak(),
        *table_of_contents(styles=renderer.styles),
        *_body_story(report_context, renderer=renderer),
    ]
    return renderer.render(
        story,
        out_path=Path(output_path) if output_path is not None else None,
        header_footer=HeaderFooterSpec(
            header_text=TITLE,
            header_center_text=HEADER_TEXT,
            header_right_text=generated_at.date().isoformat(),
            footer_text=FOOTER_TEXT,
            page_number_offset=1,
        ),
    )


def _body_story(
    report_context: RetirementSummaryPdfContext,
    *,
    renderer: PdfRenderer,
) -> list[Any]:
    styles = renderer.styles
    expense_summary = report_context.expense_summary
    charts = build_retirement_summary_chart_set(report_context)

    return [
        *section_divider(
            "Executive Summary",
            styles=styles,
            subtitle="Deterministic retirement readiness and current-data planning dashboard.",
            bookmark="executive-summary",
        ),
        navigable_heading(
            "Retirement Readiness Dashboard",
            styles=styles,
            level=1,
            bookmark="readiness-dashboard",
        ),
        paragraph(_plain_language_assessment(report_context), styles=styles),
        spacer(6),
        gauge_chart(charts.readiness_gauge, theme=renderer.theme),
        spacer(8),
        _readiness_dashboard_table(report_context, renderer=renderer),
        spacer(6),
        Paragraph(
            "Probability of success is intentionally deferred until the Monte Carlo "
            "analysis tasks add simulation-backed results.",
            styles.small,
        ),
        spacer(12),
        navigable_heading("Balance Sheet", styles=styles, level=1, bookmark="balance-sheet"),
        _balance_sheet_table(expense_summary, renderer=renderer),
        spacer(12),
        navigable_heading("Insurance", styles=styles, level=1, bookmark="insurance"),
        _insurance_table(expense_summary, renderer=renderer),
        *section_divider(
            "Planning Notes",
            styles=styles,
            subtitle=(
                "Warnings and immediate follow-up items from the current "
                "deterministic summary."
            ),
            bookmark="planning-notes",
        ),
        navigable_heading("Warnings", styles=styles, level=1, bookmark="warnings"),
        *_bullets(report_context.warnings, renderer=renderer),
        spacer(12),
        navigable_heading("Next Steps", styles=styles, level=1, bookmark="next-steps"),
        *_bullets(report_context.next_steps, renderer=renderer),
        *section_divider(
            "Appendices",
            styles=styles,
            subtitle="Reference material and report metadata for validation and troubleshooting.",
            bookmark="appendices",
        ),
        navigable_heading(
            "Appendix A - Report Metadata",
            styles=styles,
            level=1,
            bookmark="appendix-a",
        ),
        _report_metadata_table(
            report_context=report_context,
            renderer=renderer,
        ),
    ]


def _plain_language_assessment(report_context: RetirementSummaryPdfContext) -> str:
    readiness = report_context.readiness
    retirement_dates = report_context.retirement_dates
    status = _status_label(readiness.status)
    funded_ratio = _percent(readiness.funded_ratio)
    projected_assets = _currency(readiness.projected_retirement_assets)
    required_assets = _currency(readiness.required_retirement_assets)
    surplus_or_shortfall = _currency(readiness.surplus_or_shortfall)
    earliest_year = _optional_year(retirement_dates.earliest_viable_retirement_year)

    if readiness.surplus_or_shortfall >= 0:
        assessment = (
            f"The current deterministic plan appears to be on track. Projected "
            f"retirement assets of <b>{projected_assets}</b> exceed the estimated "
            f"required assets of <b>{required_assets}</b>, leaving an estimated "
            f"surplus of <b>{surplus_or_shortfall}</b>."
        )
    else:
        assessment = (
            f"The current deterministic plan shows a funding gap. Projected "
            f"retirement assets of <b>{projected_assets}</b> are below the estimated "
            f"required assets of <b>{required_assets}</b>, leaving an estimated "
            f"shortfall of <b>{surplus_or_shortfall}</b>."
        )

    return (
        f"The readiness status is <b>{status}</b> with a funded ratio of "
        f"<b>{funded_ratio}</b>. {assessment} The planned retirement year is "
        f"<b>{retirement_dates.planned_retirement_year}</b>; the earliest viable "
        f"year identified by the current deterministic date estimator is "
        f"<b>{earliest_year}</b>."
    )


def _readiness_dashboard_table(
    report_context: RetirementSummaryPdfContext,
    *,
    renderer: PdfRenderer,
) -> Table:
    rows = _readiness_dashboard_rows(report_context)
    return _number_table(rows, renderer=renderer)


def _readiness_dashboard_rows(report_context: RetirementSummaryPdfContext) -> list[list[str]]:
    readiness = report_context.readiness
    retirement_dates = report_context.retirement_dates
    expense_summary = report_context.expense_summary
    estimated_ending_estate = _estimated_ending_estate(report_context)

    rows = [
        ["Metric", "Value"],
        ["Deterministic readiness status", _status_label(readiness.status)],
        ["Funded ratio", _percent(readiness.funded_ratio)],
        ["Planned retirement year", str(retirement_dates.planned_retirement_year)],
        [
            "Earliest viable retirement year",
            _optional_year(retirement_dates.earliest_viable_retirement_year),
        ],
        ["Planning horizon", f"{readiness.planning_horizon_years} years"],
        ["Annual retirement income", _currency(expense_summary.annual_retirement_income)],
        ["Annual retirement spending", _currency(expense_summary.annual_spending_need)],
        ["Projected portfolio assets", _currency(readiness.projected_retirement_assets)],
        ["Estimated ending estate", _currency(estimated_ending_estate)],
        ["Annual withdrawal need", _currency(readiness.annual_withdrawal_need)],
        ["Estimated surplus / shortfall", _currency(readiness.surplus_or_shortfall)],
    ]
    return rows


def _report_metadata_table(
    *,
    report_context: RetirementSummaryPdfContext,
    renderer: PdfRenderer,
) -> Table:
    return simple_table(
        [
            ["Field", "Value"],
            ["Report ID", REPORT_ID],
            ["Report title", TITLE],
            ["Household", _household_name(report_context.workbook_summary.people)],
            ["Workbook path", str(report_context.workbook.path)],
            ["Workbook version", report_context.workbook_version],
            ["Engine version", report_context.engine_version],
            ["Generated at", report_context.generated_at.isoformat(timespec="seconds")],
            ["Validation status", report_context.validation_report.status],
            ["Validation failures", str(len(report_context.validation_report.failures))],
            ["Projection years", str(len(report_context.annual_projection.rows))],
        ],
        theme=renderer.theme,
    )


def _balance_sheet_table(
    expense_summary: HouseholdExpenseSummary,
    *,
    renderer: PdfRenderer,
) -> Table:
    rows = [
        ["Metric", "Value"],
        ["Retirement assets", _currency(expense_summary.retirement_assets)],
        ["Total assets", _currency(expense_summary.total_assets)],
        ["Total liabilities", _currency(expense_summary.total_liabilities)],
        ["Net worth", _currency(expense_summary.net_worth)],
    ]
    return _number_table(rows, renderer=renderer)


def _insurance_table(expense_summary: HouseholdExpenseSummary, *, renderer: PdfRenderer) -> Table:
    rows = [
        ["Metric", "Value"],
        ["Annual premiums", _currency(expense_summary.annual_insurance_premiums)],
        ["Coverage amount", _currency(expense_summary.insurance_coverage_amount)],
        ["Policies needing review", str(expense_summary.insurance_review_gap_count)],
    ]
    return _number_table(rows, renderer=renderer)


def _bullets(items: tuple[str, ...], *, renderer: PdfRenderer) -> list[Paragraph]:
    return [Paragraph(f"- {item}", renderer.styles.body) for item in items]


def _number_table(rows: list[list[str]], *, renderer: PdfRenderer) -> Table:
    table = simple_table(rows, theme=renderer.theme)
    table.setStyle(TableStyle([("ALIGN", (1, 1), (-1, -1), "RIGHT")]))
    return table


def _currency(value: Decimal) -> str:
    rounded = value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"${rounded:,.0f}"


def _percent(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * Decimal(100):,.1f}%"


def _estimated_ending_estate(report_context: RetirementSummaryPdfContext) -> Decimal:
    rows = report_context.annual_projection.rows
    if not rows:
        return Decimal(0)
    return rows[-1].ending_portfolio


def _status_label(value: str) -> str:
    return value.replace("_", " ").title()


def _optional_year(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _household_name(people: tuple[str, ...]) -> str:
    if not people:
        return "Household"
    return " and ".join(people)
