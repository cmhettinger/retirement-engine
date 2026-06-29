"""PDF renderer for the task 15 retirement summary report."""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from reportlab.platypus import PageBreak, Paragraph, Table, TableStyle

from retirement_engine.analysis import (
    HouseholdExpenseSummary,
    RetirementReadinessEstimate,
    estimate_retirement_readiness,
    summarize_household_expenses,
)
from retirement_engine.projections import RetirementDateEstimate, estimate_retirement_dates
from retirement_engine.reports.console import _next_steps, _warnings
from retirement_engine.reports.core.contracts import RenderContext, RenderResult, ReportMetadata
from retirement_engine.reports.core.renderers.pdf import (
    HeaderFooterSpec,
    PdfRenderer,
    paragraph,
    professional_letter_title_page,
    section_heading,
    spacer,
)
from retirement_engine.reports.core.renderers.pdf.tables import simple_table
from retirement_engine.workbook.reader import RetirementWorkbook
from retirement_engine.workbook.summary import summarize_retirement_workbook

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
) -> RenderResult:
    """Render a printable PDF version of the task 15 console summary report."""

    generated_at = generated_at or datetime.now().astimezone()
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
        ),
        PageBreak(),
        *_body_story(workbook, renderer=renderer, generated_date=generated_at.date()),
    ]
    return renderer.render(
        story,
        out_path=Path(output_path) if output_path is not None else None,
        header_footer=HeaderFooterSpec(header_center_text=HEADER_TEXT, footer_text=FOOTER_TEXT),
    )


def _body_story(
    workbook: RetirementWorkbook,
    *,
    renderer: PdfRenderer,
    generated_date: date,
) -> list[Any]:
    workbook_summary = summarize_retirement_workbook(workbook)
    expense_summary = summarize_household_expenses(workbook)
    readiness = estimate_retirement_readiness(workbook)
    retirement_dates = estimate_retirement_dates(workbook)
    warnings = _warnings(expense_summary, readiness)
    next_steps = _next_steps(expense_summary, readiness, retirement_dates)
    styles = renderer.styles

    return [
        section_heading("Executive Summary", styles=styles),
        paragraph(_executive_summary(expense_summary, readiness), styles=styles),
        spacer(6),
        _snapshot_table(expense_summary, readiness, retirement_dates, renderer=renderer),
        spacer(12),
        section_heading("Household", styles=styles),
        _household_table(workbook_summary.people, generated_date, renderer=renderer),
        spacer(12),
        section_heading("Balance Sheet", styles=styles),
        _balance_sheet_table(expense_summary, renderer=renderer),
        spacer(12),
        section_heading("Insurance", styles=styles),
        _insurance_table(expense_summary, renderer=renderer),
        PageBreak(),
        section_heading("Warnings", styles=styles),
        *_bullets(warnings, renderer=renderer),
        spacer(12),
        section_heading("Next Steps", styles=styles),
        *_bullets(next_steps, renderer=renderer),
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
    generated_date: date,
    *,
    renderer: PdfRenderer,
) -> Table:
    return simple_table(
        [
            ["Field", "Value"],
            ["People", ", ".join(people)],
            ["Generated date", generated_date.isoformat()],
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
