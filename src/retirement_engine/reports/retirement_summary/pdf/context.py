"""Data context for the retirement summary PDF report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from retirement_engine.analysis import (
    HouseholdExpenseSummary,
    RetirementReadinessEstimate,
    estimate_retirement_readiness,
    summarize_household_expenses,
)
from retirement_engine.calculators import (
    AssetRollup,
    CalculatedReserveRow,
    IncomeRollup,
    InsuranceRollup,
    LiabilityRollup,
    NormalizedAssetRow,
    NormalizedBudgetRow,
    NormalizedIncomeRow,
    NormalizedInsuranceRow,
    NormalizedLiabilityRow,
    ReserveRollup,
    calculate_reserve_rows,
    normalize_asset_rows,
    normalize_budget_rows,
    normalize_income_rows,
    normalize_insurance_rows,
    normalize_liability_rows,
    rollup_assets,
    rollup_income,
    rollup_insurance,
    rollup_liabilities,
    rollup_reserves,
)
from retirement_engine.config import AppConfig, load_config
from retirement_engine.projections import (
    AnnualProjection,
    RetirementDateEstimate,
    estimate_retirement_dates,
    project_retirement_years,
)
from retirement_engine.reports.console import _next_steps, _warnings
from retirement_engine.version import __version__
from retirement_engine.workbook import WorkbookValidationReport, validate_retirement_workbook
from retirement_engine.workbook.reader import RetirementWorkbook
from retirement_engine.workbook.summary import WorkbookSummary, summarize_retirement_workbook

WORKBOOK_VERSION_ROW_ID = "system.workbook.version"


@dataclass(frozen=True)
class RetirementSummaryPdfContext:
    """Reusable report inputs gathered before PDF page rendering begins."""

    workbook: RetirementWorkbook
    config: AppConfig
    generated_at: datetime
    engine_version: str
    workbook_version: str
    workbook_summary: WorkbookSummary
    expense_summary: HouseholdExpenseSummary
    readiness: RetirementReadinessEstimate
    annual_projection: AnnualProjection
    retirement_dates: RetirementDateEstimate
    validation_report: WorkbookValidationReport
    budget_rows: tuple[NormalizedBudgetRow, ...]
    reserve_rows: tuple[CalculatedReserveRow, ...]
    income_rows: tuple[NormalizedIncomeRow, ...]
    asset_rows: tuple[NormalizedAssetRow, ...]
    liability_rows: tuple[NormalizedLiabilityRow, ...]
    insurance_rows: tuple[NormalizedInsuranceRow, ...]
    reserve_rollup: ReserveRollup
    income_rollup: IncomeRollup
    asset_rollup: AssetRollup
    liability_rollup: LiabilityRollup
    insurance_rollup: InsuranceRollup
    warnings: tuple[str, ...]
    next_steps: tuple[str, ...]


def build_retirement_summary_pdf_context(
    workbook: RetirementWorkbook,
    *,
    generated_at: datetime,
    config: AppConfig | None = None,
) -> RetirementSummaryPdfContext:
    """Gather all current-data report inputs in one reusable structure."""

    app_config = config or load_config()
    workbook_summary = summarize_retirement_workbook(workbook)
    expense_summary = summarize_household_expenses(workbook)
    readiness = estimate_retirement_readiness(workbook)
    annual_projection = project_retirement_years(workbook, start_year=generated_at.year)
    retirement_dates = estimate_retirement_dates(workbook)
    validation_report = validate_retirement_workbook(workbook, app_config)

    budget_rows = normalize_budget_rows(workbook.sheet("Budget").rows)
    reserve_rows = calculate_reserve_rows(workbook.sheet("Reserves").rows)
    income_rows = normalize_income_rows(workbook.sheet("Income").rows)
    asset_rows = normalize_asset_rows(workbook.sheet("Assets").rows)
    liability_rows = normalize_liability_rows(workbook.sheet("Liabilities").rows)
    insurance_rows = normalize_insurance_rows(workbook.sheet("Insurance").rows)

    return RetirementSummaryPdfContext(
        workbook=workbook,
        config=app_config,
        generated_at=generated_at,
        engine_version=__version__,
        workbook_version=_workbook_version(workbook),
        workbook_summary=workbook_summary,
        expense_summary=expense_summary,
        readiness=readiness,
        annual_projection=annual_projection,
        retirement_dates=retirement_dates,
        validation_report=validation_report,
        budget_rows=budget_rows,
        reserve_rows=reserve_rows,
        income_rows=income_rows,
        asset_rows=asset_rows,
        liability_rows=liability_rows,
        insurance_rows=insurance_rows,
        reserve_rollup=rollup_reserves(reserve_rows),
        income_rollup=rollup_income(income_rows),
        asset_rollup=rollup_assets(asset_rows),
        liability_rollup=rollup_liabilities(liability_rows),
        insurance_rollup=rollup_insurance(insurance_rows),
        warnings=_warnings(expense_summary, readiness),
        next_steps=_next_steps(expense_summary, readiness, retirement_dates),
    )


def _workbook_version(workbook: RetirementWorkbook) -> str:
    assumptions = workbook.sheets.get("Assumptions")
    if assumptions is None:
        return "unknown"
    version_row = assumptions.rows_by_id.get(WORKBOOK_VERSION_ROW_ID)
    if version_row is None:
        return "unknown"
    value = version_row.values.get("Value")
    if value is None:
        return "unknown"
    return str(value)


__all__ = [
    "RetirementSummaryPdfContext",
    "build_retirement_summary_pdf_context",
]
