# Retirement Engine TODO

> **Project Status:** Initial workbook prototype complete.
>
> This TODO tracks the planned Python functionality buildout. Items are intentionally scoped so each row should be achievable in a single focused Codex session.

## Buildout Plan

| Order | Category | Task | Description | Status |
|------:|----------|------|-------------|--------|
| 0-A | Environment | Configuration framework | Implement configuration loading from `env/config.yml`. Define the application's configuration model and validate required settings. Initially include items such as supported workbook version, default workbook path, default output directory, and report options. | Complete |
| 0-B | Environment | Application bootstrap | Implement application startup, configuration loading, logging, build directory creation, and common initialization. This provides a consistent entry point for all CLI commands before workbook processing begins. | Complete |
| 1 | Workbook | Workbook reader | Implement workbook loading for `template.xlsx`-compatible files using `openpyxl`. Parse each sheet into structured Python data without performing financial calculations. | Complete |
|     2 | Workbook      | Workbook validation               | Validate required sheets, required columns, workbook version, stable IDs, duplicate IDs, missing required rows, and invalid Yes/No fields. Return clear human-readable validation errors.                                             | Complete |
|     3 | Workbook      | Internal data model               | Define simple internal Python structures for assumptions, budget rows, reserve rows, income rows, assets, liabilities, and insurance. Keep these independent from Excel.                                                              | Not Started |
|     4 | CLI           | Basic command-line interface      | Implement the initial CLI with validate and summarize commands. Both commands should support human-readable output by default and structured output formats (such as JSON) via command-line options. Additional commands (project, monte-carlo, optimize, report, migrate) will be added in later phases.  | Not Started |
|     5 | Calculators   | Budget normalization              | Normalize budget rows where users may enter annual, monthly, or both. Calculate annual and monthly equivalents without modifying the workbook.                                                                                        | Not Started |
|     6 | Calculators   | Income normalization              | Normalize income rows where users may enter annual, monthly, or both. Calculate annual and monthly equivalents and taxable/non-taxable rollups.                                                                                       | Not Started |
|     7 | Calculators   | Reserve calculation               | Calculate annual and monthly replacement reserve needs from replacement cost, expected useful life, current age, remaining useful life, and next replacement year.                                                                    | Not Started |
|     8 | Calculators   | Assets rollup                     | Calculate household asset totals by owner, account type, and tax treatment, including pre-tax, Roth, taxable, cash, HSA, and real estate groupings.                                                                                   | Not Started |
|     9 | Calculators   | Liabilities rollup                | Calculate total liabilities, monthly debt payments, payoff-year visibility, and net worth impact.                                                                                                                                     | Not Started |
|    10 | Calculators   | Insurance summary                 | Summarize insurance policies, annual premiums, coverage amounts, and policy gaps that may need review.                                                                                                                                | Not Started |
|    11 | Core Analysis | Retirement expense summary        | Combine budget, income, reserves, assets, liabilities, and insurance into a single household summary showing annual spending need, monthly spending need, must-pay spending, optional spending, and replacement reserve contribution. | Not Started |
|    12 | Core Analysis | Retirement readiness estimate     | Estimate whether current assets, contributions, assumptions, and income sources appear sufficient to support projected retirement expenses. Keep the first version simple and deterministic.                                          | Not Started |
|    13 | Projections   | Year-by-year projection engine    | Build a simple annual projection model for assets, income, expenses, inflation, contributions, retirement date, and portfolio balances.                                                                                               | Not Started |
|    14 | Projections   | Retirement date estimator         | Estimate potential retirement dates based on current age, assets, contributions, expected returns, projected expenses, and expected income.                                                                                           | Not Started |
|    15 | Reports       | Console summary report            | Generate a clean text summary suitable for CLI output, including key numbers, warnings, and next-step planning notes.                                                                                                                 | Not Started |
|    16 | Reports       | HTML report                       | Generate an initial HTML report under `build/` with retirement expense totals, reserve needs, income, assets, liabilities, and readiness summary.                                                                                     | Not Started |
|    17 | Reports       | Charts                            | Add basic charts for annual expenses, income mix, asset allocation by tax treatment, reserves, and projected portfolio balance.                                                                                                       | Not Started |
|    18 | Reports       | PDF report                        | Generate a printable PDF retirement summary using the calculated results and static assets from `resources/`.                                                                                                                         | Not Started |
|    19 | Simulations   | Monte Carlo prototype             | Implement a first-pass Monte Carlo simulation for portfolio success probability using configurable return assumptions and retirement expenses.                                                                                        | Not Started |
|    20 | Simulations   | Sequence-of-returns analysis      | Add deterministic bad-market scenarios to show how early retirement losses affect portfolio durability.                                                                                                                               | Not Started |
|    21 | Optimization  | Withdrawal strategy prototype     | Compare simple withdrawal strategies across taxable, pre-tax, Roth, and cash accounts.                                                                                                                                                | Not Started |
|    22 | Optimization  | Roth conversion analysis          | Prototype Roth conversion scenarios using simplified tax assumptions.                                                                                                                                                                 | Not Started |
|    23 | Optimization  | Social Security claiming analysis | Compare basic claiming-age scenarios for one- and two-person households.                                                                                                                                                              | Not Started |
|    24 | Taxes         | Tax model prototype               | Add a simplified tax-estimation module based on taxable income, withdrawals, Social Security treatment, and configured tax assumptions.                                                                                               | Not Started |
|    25 | Tools         | Workbook migration support        | Add tooling to detect older workbook versions and migrate them forward when the template structure changes.                                                                                                                           | Not Started |
|    26 | Tools         | Example workbook generator        | Generate `resources/workbooks/example.xlsx` from fake/sample data so tests and documentation can use a non-private workbook.                                                                                                          | Complete    |
|    27 | Testing       | Test suite foundation             | Add pytest coverage for workbook parsing, validation, normalization, reserve calculations, rollups, and core projections.                                                                                                             | Not Started |
|    28 | Documentation | User workflow docs                | Document how to copy `resources/workbooks/template.xlsx`, fill out a personal workbook, avoid committing private files, and run validation/summary commands.                                                                          | Not Started |
|    29 | Documentation | Calculation docs                  | Document how major calculations work, especially budget normalization, reserves, projections, retirement readiness, and Monte Carlo assumptions.                                                                                      | Not Started |
|    30 | Future UI     | Interactive dashboard             | Consider a lightweight dashboard after the core engine is stable. This should consume the same calculation modules and not duplicate business logic.                                                                                  | Future      |

## Near-Term Priority

The next practical build sequence should be:

1. Workbook reader
2. Workbook validation
3. Internal data model
4. CLI validation command
5. Budget normalization
6. Income normalization
7. Reserve calculation
8. Basic household summary

Once those are working, the project can produce useful retirement expense estimates before moving into projections, simulations, and optimization.
