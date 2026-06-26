# Retirement Engine

> ⚠️ **Project Status: Very Early Development**
>
> Retirement Engine is in the earliest stages of design and development. At this point the repository primarily contains architectural ideas, workbook design, and planning documents. **It is not yet functional software and should not be relied upon for financial planning or investment decisions.**

## Overview

Retirement Engine is intended to be a reusable Python engine for modeling retirement readiness and long-term financial planning.

The long-term vision is to separate:

* A human-friendly Excel workbook used to capture household financial information.
* A Python calculation engine that performs analysis.
* Reporting components that generate summaries, projections, charts, and PDFs.

The workbook is intended to serve as the primary data model for the engine.

For workbook structure and template conventions, see [docs/workbook.md](docs/workbook.md).

## Planned Features

* Retirement expense planning
* Replacement reserve planning
* Retirement income modeling
* Asset and liability tracking
* Retirement readiness projections
* Portfolio growth projections
* Withdrawal strategy analysis
* Social Security optimization
* Tax-aware retirement planning
* Monte Carlo simulations
* PDF and HTML reporting

## Project Philosophy

A few guiding principles drive the design:

* Keep the workbook simple and easy for humans to edit.
* Keep business logic in Python, not Excel formulas.
* Make calculations deterministic, testable, and reusable.
* Separate workbook I/O from financial calculations.
* Build modular components that can evolve independently.

## Current Status

The current focus is designing:

* Workbook structure
* Workbook schema
* Calculation architecture
* Project layout
* Reporting framework

Implementation will follow once the workbook design has stabilized.

## Repository Layout

```text
env/          Configuration
resources/    Workbook templates and static assets
src/          Retirement Engine source code
tests/        Automated tests
docs/         Project documentation
tools/        Developer utilities
bin/          Helper scripts
build/        Generated artifacts (not tracked)
```

## License

Retirement Engine is an educational and planning tool only. It does not provide financial, tax, legal, or investment advice. Users are responsible for verifying all assumptions and consulting qualified professionals before making financial decisions.

The goal is to make the project freely available for:

- Personal use
- Educational use
- Learning
- Experimentation

Commercial use requires separate permission from the copyright holder.

See the LICENSE file for the complete license text.
