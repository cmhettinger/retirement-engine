"""PDF renderer for the retirement summary report."""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from reportlab.platypus import PageBreak, Paragraph, Table, TableStyle

from retirement_engine.analysis import (
    HouseholdExpenseSummary,
    RetirementReadinessEstimate,
)
from retirement_engine.config import AppConfig
from retirement_engine.projections import RetirementDateEstimate
from retirement_engine.reports.core.contracts import RenderContext, RenderResult, ReportMetadata
from retirement_engine.reports.core.renderers.pdf import (
    HeaderFooterSpec,
    PdfRenderer,
    navigable_heading,
    paragraph,
    professional_letter_title_page,
    section_divider,
    spacer,
    table_of_contents,
)
from retirement_engine.reports.core.renderers.pdf.tables import simple_table
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
    readiness = report_context.readiness
    retirement_dates = report_context.retirement_dates

    return [
        *section_divider(
            "Executive Summary",
            styles=styles,
            subtitle="Current readiness, balance-sheet snapshot, and near-term planning notes.",
            bookmark="executive-summary",
        ),
        paragraph(_executive_summary(expense_summary, readiness), styles=styles),
        spacer(6),
        _snapshot_table(expense_summary, readiness, retirement_dates, renderer=renderer),
        spacer(12),
        navigable_heading("Household", styles=styles, level=1, bookmark="household"),
        _household_table(
            report_context.workbook_summary.people,
            report_context.generated_at,
            workbook_version=report_context.workbook_version,
            engine_version=report_context.engine_version,
            renderer=renderer,
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


def _executive_summary(
    expense_summary: HouseholdExpenseSummary,
    readiness: RetirementReadinessEstimate,
) -> str:
    status = readiness.status.replace("_", " ")
    return (
        f"The deterministic retirement summary is currently <b>{status}</b>. "
        f"Annual spending need is <b>{_currency(expense_summary.annual_spending_need)}</b>, "
        f"annual withdrawal need is <b>{_currency(readiness.annual_withdrawal_need)}</b>, "
        f"and the estimated surplus or shortfall is "
        f"<b>{_currency(readiness.surplus_or_shortfall)}</b>."
    )


def _snapshot_table(
    expense_summary: HouseholdExpenseSummary,
    readiness: RetirementReadinessEstimate,
    retirement_dates: RetirementDateEstimate,
    *,
    renderer: PdfRenderer,
) -> Table:
    rows = [
        ["Metric", "Value"],
        ["Annual spending need", _currency(expense_summary.annual_spending_need)],
        ["Monthly spending need", _currency(expense_summary.monthly_spending_need)],
        ["Must-pay annual spending", _currency(expense_summary.annual_must_pay_spending)],
        ["Optional annual spending", _currency(expense_summary.annual_optional_spending)],
        ["Replacement reserve", _currency(expense_summary.annual_replacement_reserve)],
        ["Estimated income", _currency(expense_summary.annual_retirement_income)],
        ["Annual withdrawal need", _currency(readiness.annual_withdrawal_need)],
        ["Status", readiness.status.replace("_", " ")],
        ["Planned retirement year", str(retirement_dates.planned_retirement_year)],
        ["Earliest viable year", _optional_year(retirement_dates.earliest_viable_retirement_year)],
        ["Funded ratio", _percent(readiness.funded_ratio)],
    ]
    return _number_table(rows, renderer=renderer)


def _household_table(
    people: tuple[str, ...],
    generated_at: datetime,
    *,
    workbook_version: str,
    engine_version: str,
    renderer: PdfRenderer,
) -> Table:
    return simple_table(
        [
            ["Field", "Value"],
            ["People", _household_name(people)],
            ["Workbook version", workbook_version],
            ["Engine version", engine_version],
            ["Generated date", generated_at.date().isoformat()],
            ["Generated time", generated_at.isoformat(timespec="seconds")],
        ],
        theme=renderer.theme,
    )


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


def _optional_year(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _household_name(people: tuple[str, ...]) -> str:
    if not people:
        return "Household"
    return " and ".join(people)

