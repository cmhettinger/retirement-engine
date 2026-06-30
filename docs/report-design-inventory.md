# PDF Report Design Inventory

**Status:** Task 17 inventory complete

This document maps `docs/report-design.md` to the engine data and report
infrastructure available today. Its purpose is to separate report pages that can be
built now from pages that need later simulations, optimization, tax modeling, or
workbook changes.

## Readiness Key

| Status | Meaning |
| --- | --- |
| Ready now | The workbook data and engine outputs already exist. Implementation is mostly PDF composition, table layout, copy, or chart rendering. |
| Partial | Some data exists, but the report section needs a new derived summary, chart adapter, narrative rule, or presentation helper. |
| Future | The section depends on future analytical models, simulations, optimization, tax logic, healthcare logic, or workbook sheets. |

## Current Data And Report Sources

| Source | Available today | Useful report sections |
| --- | --- | --- |
| `workbook.reader.RetirementWorkbook` | Parsed workbook sheets and raw rows keyed by stable IDs. | Appendix E, methodology, detailed source-value tables. |
| `workbook.summary.WorkbookSummary` | People, row counts, annual expenses, reserves, income, and retirement assets. | Cover, household snapshot, executive summary. |
| `analysis.expense_summary.HouseholdExpenseSummary` | Spending need, budget spending, must-pay spending, optional spending, replacement reserves, income gap, assets, liabilities, net worth, debt payments, insurance totals, and insurance review gaps. | Executive summary, current financial picture, retirement spending, insurance, action plan. |
| `analysis.readiness.RetirementReadinessEstimate` | Deterministic readiness status, timeline, horizon, return/inflation assumptions, projected assets, withdrawal need, required assets, cash reserve target, estate target, surplus/shortfall, and funded ratio. | Readiness dashboard, assumptions, methodology, action plan. |
| `projections.annual.AnnualProjection` | Year-by-year ages, retirement flag, starting portfolio, contributions, investment return, expenses, income, withdrawal, ending portfolio, and depletion year. | Lifetime cash flow, long-term projection, annual projection appendix, portfolio growth. |
| `projections.retirement_date.RetirementDateEstimate` | Planned retirement year, earliest viable year, and candidate years with ending portfolio and surplus/shortfall. | Readiness dashboard, retirement timeline, action plan. |
| `calculators.assets` | Normalized account rows and rollups by owner, account type, tax treatment, and tax bucket. | Financial snapshot, investment portfolio, tax diversification, account appendix. |
| `calculators.budget` | Normalized budget rows by category/item with annual and monthly equivalents and must-pay classification. | Retirement budget, spending breakdown, workbook-values appendix. |
| `calculators.income` | Normalized income rows and taxable/non-taxable rollups. | Current income, retirement income overview, income-source charts. |
| `calculators.reserves` | Calculated replacement reserve rows, annual/monthly contribution, remaining life, and next replacement year. | Retirement spending, reserves appendix, action plan. |
| `calculators.liabilities` | Normalized liabilities, debt payments, payoff years, and rollups by owner/type. | Financial snapshot, liabilities appendix, retirement timeline. |
| `calculators.insurance` | Normalized policies, premiums, coverage, owner/type rollups, and missing-field review gaps. | Insurance summary, action plan, appendix. |
| `workbook.validation.WorkbookValidationReport` | Schema, version, stable ID, duplicate ID, required row, and Yes/No validation failures. | Action plan, methodology, workbook-values appendix. |
| `config.AppConfig` and `version.__version__` | Supported workbook version, application version, report options, output directory. | Cover, methodology. |
| `reports.retirement_summary.pdf.render` | Current PDF cover page and compact executive/body report. | Foundation for all task 18+ report work. |
| `reports.core.renderers.pdf` | ReportLab document, styles, tables, image helpers, chart image flowable, branding, and title page primitives. | PDF shell, typography, tables, image/chart placement. |
| `tmp/reporting` | Reference stonks chart-generation and report-component code. | Task 20 chart migration only; do not keep runtime dependencies on `tmp/`. |

## Report Structure Inventory

| Design item | Readiness | Current sources | Missing or follow-up work |
| --- | --- | --- | --- |
| Cover page | Partial | Current PDF already has a professional title page; people are available from `WorkbookSummary`; workbook version comes from the `Assumptions` sheet; engine version comes from config/version. Branding assets exist under `resources/branding`. | Add household names, workbook version, engine version, generation date, and selected branding artwork to the existing cover without losing the current style. |
| Table of contents | Future | PDF rendering infrastructure exists. | Add TOC/page-number support to the PDF shell. This is layout work, not financial-model work. |
| Executive summary - readiness dashboard | Partial | `RetirementReadinessEstimate`, `RetirementDateEstimate`, `HouseholdExpenseSummary`, and `AnnualProjection`. | Deterministic dashboard can be built now. True probability of success and Monte Carlo gauge wait for task 27/28. Gauge visuals wait for chart support. |
| Executive summary - key findings and recommendations | Partial | Console `_warnings` and `_next_steps`; validation failures; readiness shortfall/surplus; insurance gaps; liability and reserve summaries. | Add a report-facing findings/recommendation builder with evidence-backed wording and priorities. Some recommendations, such as Roth conversions and Social Security timing, wait for later analysis tasks. |
| Household financial snapshot | Ready now | Asset, liability, net worth, retirement asset, debt payment, cash/tax bucket, and insurance totals. | Build tables/charts. Cash reserve can use the cash asset bucket plus desired cash reserve, but there is no separate emergency-fund model yet. |
| Investment portfolio | Partial | Asset rows include owner, account type, institution, balance, contribution, employer match, and tax treatment. Rollups exist by account type and tax bucket. | Account/tax-treatment pages can be built now. Detailed holdings and security-level allocation require a future holdings sheet or integration. |
| Current income and savings | Partial | Income rows and taxable rollups; asset annual contributions and employer match. | Income-source and contribution pages can be built now. Savings rate requires defining income denominator and possibly current-spending treatment. |
| Retirement income overview | Partial | Income rows, annual retirement income total, projection income, and projection withdrawal need. | Basic income overview can be built now. Social Security/pension/annuity/rental specificity depends on workbook source labels until typed retirement-income modeling exists. |
| Social Security strategy | Future | Income rows may contain Social Security-like sources if entered manually. | Claiming ages, benefit by claiming age, spousal/survivor benefits, and claiming comparisons wait for Social Security analysis. |
| Withdrawal strategy | Future | Projection rows include total annual withdrawal; assets include tax buckets. | Withdrawal order and withdrawals by taxable/pre-tax/Roth/cash wait for withdrawal strategy optimization. |
| Retirement budget | Ready now | Normalized budget rows and household spending summary. | Build category/item tables, must-pay/optional split, reserve inclusion, and spending breakdown charts. |
| Retirement spending model comparison | Future | Current projection uses one inflation-adjusted spending path from current budget/reserves. | Multiple spending models wait for new workbook sheets and spending model engine tasks. |
| Lifetime cash flow | Partial | `AnnualProjection` has income, expenses, withdrawals, contributions, investment return, and ending portfolio. | Build annual summary table and charts. Taxes are not modeled yet, so tax and after-tax cash flow columns should be omitted or clearly marked unavailable. |
| Lifetime financial projection | Partial | `AnnualProjection` rows have year, ages, income, expenses, withdrawal, and ending portfolio. | Build tables/charts now. Taxes wait for tax model. |
| Portfolio growth | Ready now | `AnnualProjection` rows include starting portfolio, investment return, contributions, withdrawals, ending portfolio. | Build portfolio balance, annual withdrawal, and cumulative withdrawal charts after chart migration. |
| Estate projection | Partial | `RetirementReadinessEstimate.desired_estate_value`; `AnnualProjection` ending portfolio; `RetirementDateCandidate` ending portfolio. | Selected-age estate table and ending-portfolio chart can be built now as a deterministic projection. A richer legacy/estate model is future. |
| Tax analysis | Future | Income taxability exists for income rows; asset tax treatment exists. | Federal/state tax, effective/marginal rates, capital gains, and taxes by year wait for tax model. |
| Healthcare and Medicare | Future | Budget categories may contain healthcare/insurance expenses if entered by the user. | Medicare enrollment, IRMAA, premium estimates, long-term care assumptions, and healthcare inflation need future workbook/model support. |
| Monte Carlo summary | Future | No simulation engine yet. | Wait for Monte Carlo prototype and report integration tasks. |
| Scenario analysis | Future | Retirement-date candidates provide limited deterministic timing sensitivity. | Poor-market, high-inflation, longevity, healthcare, and retirement-age scenarios wait for scenario/sequence analysis tasks. |
| Sensitivity analysis | Future | No tornado/sensitivity engine yet. | Wait for sensitivity analysis implementation after core simulations/scenarios. |
| Recommended actions | Partial | Warnings, next steps, validation failures, readiness, insurance gaps, reserve needs, debt payments, and retirement-date outputs. | Build now for current evidence. More sophisticated tax, Roth, Social Security, healthcare, and withdrawal recommendations wait for those models. |
| Retirement timeline | Partial | Planned retirement year, earliest viable year, liability payoff years, reserve next replacement years, and projection years. | Timeline can be built now for current events. Social Security, Medicare, pension, and RMD milestones need additional assumptions/modeling. |
| Planning assumptions | Partial | Assumptions sheet, readiness assumptions, config supported workbook version, application version. | Build an assumptions/methodology page now. Add tax, healthcare, Social Security, and spending-model assumptions later. |
| Methodology | Ready now | Config, workbook version, engine version, report generation date, current deterministic calculator/projection modules. | Document current limitations clearly, especially no Monte Carlo/tax/withdrawal strategy yet. |
| Appendix A - Annual Projection | Partial | `AnnualProjection.rows`. | Build now with available columns. Taxes column waits for tax model. |
| Appendix B - Account Summary | Ready now | Normalized asset rows and rollups. | Build account table now. |
| Appendix C - Investment Holdings | Future | No holdings worksheet or security parser exists. | Requires future workbook enhancement or integration. |
| Appendix D - Insurance Summary | Ready now | Normalized insurance rows and rollups. | Build policy table and gaps now. |
| Appendix E - Workbook Values | Ready now | Raw workbook sheets/rows plus normalized/calculated values. | Build selected source-value and interpreted-value tables. |

## Chart Inventory

These chart candidates can be built from current data after task 20 provides a
native chart-generation module:

| Chart | Current source | Readiness |
| --- | --- | --- |
| Readiness/funded ratio gauge | `RetirementReadinessEstimate.funded_ratio` | Partial; chart migration needed. |
| Spending breakdown | Normalized budget rows and reserve rollup | Ready after chart migration. |
| Must-pay vs optional spending | `HouseholdExpenseSummary` | Ready after chart migration. |
| Income mix | Normalized income rows and taxable rollups | Ready after chart migration. |
| Asset allocation by tax treatment | `AssetRollup.by_tax_treatment` / `by_tax_bucket` | Ready after chart migration. |
| Net worth allocation | Asset/liability rollups | Ready after chart migration. |
| Portfolio balance over time | `AnnualProjection.rows` | Ready after chart migration. |
| Income vs expenses | `AnnualProjection.rows` | Ready after chart migration. |
| Annual surplus/deficit | `AnnualProjection.rows` derived as income minus expenses | Ready after chart migration. |
| Annual withdrawals and cumulative withdrawals | `AnnualProjection.rows` | Ready after chart migration. |
| Monte Carlo distribution/percentiles | Not available | Future. |
| Sensitivity tornado | Not available | Future. |
| Spending model overlay | Not available | Future. |

## Follow-On TODO Reconciliation

The current follow-on tasks in `docs/todo.md` are broadly in the right order, with
these refinements:

1. Task 18 should focus on report shell/navigation and should preserve the existing
   cover-page visual direction while adding the missing cover fields.
2. Task 19 should create a reusable report data context before charts/pages so
   page renderers do not each recompute or reinterpret workbook/calculator data.
3. Task 20 should be specifically about native chart generation, not just embedding
   chart images. `ChartBlock` already embeds image files; the missing piece is
   generating retirement-engine charts from engine data.
4. Tasks 21-34 can proceed before Monte Carlo, taxes, withdrawal optimization, and
   workbook spending-model sheets. They should omit unavailable columns or label
   them as future rather than fabricating placeholder values.
5. Tasks 36, 40, 42, 45, 47, 49, 51, and 60 are correctly placed after their underlying
   analytical tasks.
6. Future workbook spending-model tasks should stay at the end of the TODO because
   the current report can become substantially better with existing data first.

## Recommended Immediate Build Sequence

1. Complete task 18 by creating a reusable multi-section PDF shell with TOC,
   sectioning, page numbering, methodology, and appendix support.
2. Complete task 19 by adding a report data context that gathers all current
   workbook, calculator, projection, validation, config, and version data needed
   by the PDF.
3. Complete task 20 by adding native chart-generation helpers under
   `src/retirement_engine/reports/core/` and first chart specs for current data.
4. Build tasks 21-24 as the first content wave: readiness, findings, and current
   financial picture.
5. Build tasks 25-33 as the second content wave: portfolio, income, spending,
   cash flow, projections, timeline, methodology, and appendices.
6. Complete task 34 with render-and-verify polish against the sample workbook and a
   private workbook path.
