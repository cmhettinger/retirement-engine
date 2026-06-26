# Retirement Engine Overview

> **Project Status:** Pre-Alpha
>
> Retirement Engine is currently in the architecture and design phase. The workbook structure, project layout, and calculation engine are being designed before implementation begins. The repository should be considered an evolving prototype rather than production-ready software.

## Vision

Retirement Engine is a Python-based financial modeling engine designed to help individuals and families estimate retirement readiness through a combination of spreadsheet-based data entry and reusable calculation modules.

Unlike many retirement calculators that require users to enter data into a website, Retirement Engine uses an Excel workbook as the primary financial model. The workbook serves as a long-lived representation of a household's financial situation, while the Python engine performs calculations, projections, simulations, and reporting.

The long-term goal is to build a transparent, extensible retirement modeling platform rather than a single retirement calculator.

---

# Design Philosophy

Several principles guide the design of Retirement Engine.

## Workbook-Driven

The Excel workbook is the project's primary data model.

Users should be able to understand and edit their financial information directly within the workbook without needing to understand Python or internal implementation details.

The workbook is intended to remain relatively simple and stable over time.

---

## Keep Excel Simple

Excel is excellent for entering data.

Excel is less suitable for implementing complex financial logic.

Excel files can easily be shared with a retirement planning professional.

Retirement Engine intentionally keeps workbook formulas to a minimum.

The workbook captures facts and assumptions while Python performs calculations.

This separation makes the financial engine easier to maintain, test, and extend.

---

## Modular Calculation Engine

Financial calculations are implemented as independent modules.

Examples include:

* Budget calculations
* Replacement reserve calculations
* Retirement date estimation
* Portfolio projections
* Monte Carlo simulation
* Tax modeling
* Withdrawal optimization
* Social Security optimization

Each module should remain independent and reusable.

---

## Reporting Is Separate

Reports should never contain business logic.

The engine performs calculations first.

Reports simply present results in formats such as:

* Console output
* HTML
* PDF
* Charts
* Future web interfaces

---

# Workbook Structure

The workbook is planned to contain several logical worksheets.

## Assumptions

Global planning assumptions.

Examples include:

* Current ages
* Planned retirement ages
* Life expectancy
* Social Security claiming ages
* Inflation assumptions
* Investment return assumptions
* Tax assumptions
* Planning horizon

---

## Budget

Annual recurring household expenses.

Categories include:

* Housing
* Utilities
* Food
* Healthcare
* Insurance
* Taxes
* Transportation
* Communications
* Personal
* Family
* Recreation
* Pets
* Financial
* Debt
* Legal
* Memberships
* Replacement Reserve (annual contribution)
* Other

Each budget line contains:

* Required vs optional indicator
* Category
* Item
* Annual amount
* Monthly equivalent
* Stable identifier

---

## Replacement Reserve

A planning worksheet for future replacement costs.

Rather than estimating monthly savings directly, users enter information such as:

* Replacement cost
* Expected useful life
* Current age
* Remaining useful life

The calculation engine determines recommended annual reserve contributions.

Examples include:

* Roof
* HVAC
* Appliances
* Vehicles
* Furniture
* Computers
* Electronics
* Medical contingency
* Emergency reserve

---

## Income

Retirement income sources.

Examples include:

* Social Security
* Pension
* IRA withdrawals
* 401(k) withdrawals
* Brokerage income
* Rental income
* Employment income

---

## Assets

Retirement assets and investment accounts.

Examples include:

* 401(k)
* Traditional IRA
* Roth IRA
* Brokerage accounts
* Savings
* Cash reserves

---

## Liabilities

Outstanding debt and future obligations.

Examples include:

* Mortgage
* Vehicle loans
* Personal loans
* Credit cards

---

## Insurance

Insurance policies relevant to retirement planning.

Examples include:

* Health insurance
* Long-term care insurance
* Life insurance
* Umbrella coverage

---

# Planned Features

The project is intended to grow in phases.

## Phase 1

Core retirement planning.

* Workbook validation
* Budget calculations
* Reserve calculations
* Income calculations
* Retirement readiness estimation

---

## Phase 2

Projection engine.

* Portfolio growth projections
* Annual cash-flow modeling
* Retirement date estimation
* Withdrawal planning

---

## Phase 3

Optimization.

* Safe withdrawal strategies
* Roth conversion analysis
* Tax-aware withdrawal optimization
* Social Security optimization

---

## Phase 4

Simulation.

* Monte Carlo retirement analysis
* Sequence-of-returns risk
* Success probability calculations
* Scenario comparison

---

## Phase 5

Reporting.

* Executive summaries
* PDF reports
* Charts and visualizations
* HTML reports
* Optional interactive dashboard

---

# Project Architecture

The project follows many of the engineering conventions used by the Empire projects.

Repository structure is intentionally modular.

* `env/` — configuration
* `resources/` — workbook templates and static assets
* `docs/` — project documentation
* `src/` — application source code
* `tests/` — automated tests
* `tools/` — developer utilities
* `bin/` — helper scripts
* `build/` — generated artifacts (ephemeral)

Business logic is organized into focused modules that separate workbook I/O, financial calculations, simulations, optimization, and reporting.

---

# Versioning

The application version lives in the root `VERSION` file and is used for Python
package metadata and runtime version reporting.

The workbook schema version is separate. It is stored inside the workbook on the
`Assumptions` sheet as `system.workbook.version`.

`env/config.yml` should reference the supported workbook schema version, not the
application version. These values may match in early development, but they represent
different concepts.

---

# Long-Term Goals

Retirement Engine is intended to become a reusable financial modeling platform rather than a single retirement calculator.

Potential future capabilities include:

* Multiple household models
* Scenario comparison
* Retirement timing analysis
* Tax forecasting
* Estate planning support
* Healthcare cost projections
* Inflation modeling
* Report generation
* Interactive dashboards
* Additional import/export formats

The guiding philosophy is to keep the workbook as the authoritative source of household financial data while allowing the Python engine to evolve with increasingly sophisticated planning and analysis capabilities.
