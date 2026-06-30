# Retirement Engine Report Design

**Status:** Draft Design Specification

This document defines the overall structure of the Retirement Engine PDF report. It serves as the canonical reference for report organization, page contents, charts, tables, and workbook requirements.

The goal is to produce a report comparable to what a professional financial planner would deliver after building a comprehensive retirement plan. The report should tell the story of the client's retirement, not simply present calculations.

---

# Design Philosophy

The report should answer the user's questions in a logical order:

1. Where am I today?
2. Can I retire?
3. How will retirement work?
4. What risks should I understand?
5. What actions should I take?
6. How were these results calculated?

Each section should begin with a short narrative explaining what the data means before presenting the supporting tables and charts.

---

# Report Structure

## Cover Page

Purpose

A clean, professional cover page.

Contents

* Retirement Planning Report
* Household name(s)
* Report generation date
* Workbook version
* Engine version
* Optional branding artwork

---

## Table of Contents

Purpose

Automatically generated list of report sections and page numbers.

---

# Section 1 – Executive Summary

## Retirement Readiness Dashboard

Purpose

Provide an immediate answer to the question:

> "Am I ready to retire?"

Contents

* Retirement readiness score
* Probability of success
* Planned retirement age
* Planning horizon
* Estimated annual retirement income
* Estimated annual retirement spending
* Estimated ending estate
* Overall assessment

Charts

* Retirement readiness gauge
* Monte Carlo success gauge

---

## Key Findings & Recommendations

Purpose

Summarize the most important observations from the plan.

Contents

### Strengths

Examples

* Retirement appears financially sustainable.
* Portfolio provides a comfortable safety margin.

### Risks

Examples

* Healthcare inflation
* Sequence-of-returns risk
* High spending early in retirement

### Recommended Actions

Examples

* Delay Social Security
* Increase retirement savings
* Complete Roth conversions
* Pay off mortgage before retirement

---

# Section 2 – Current Financial Picture

## Household Financial Snapshot

Purpose

Summarize today's financial position.

Tables

* Assets
* Liabilities
* Net worth
* Cash reserves

Charts

* Net worth allocation
* Asset allocation

---

## Investment Portfolio

Purpose

Summarize investment accounts.

Tables

* Account balances
* Account types
* Tax treatment
* Asset allocation

Charts

* Asset allocation
* Tax diversification

---

## Current Income & Savings

Purpose

Summarize current earnings and retirement savings.

Tables

* Employment income
* Pension
* Savings rate
* Annual contributions

Charts

* Income sources
* Savings allocation

---

# Section 3 – Retirement Income Plan

## Retirement Income Overview

Purpose

Explain where retirement income will originate.

Tables

* Social Security
* Pension
* Annuities
* Rental income
* Portfolio withdrawals
* Other income

Charts

* Lifetime income timeline

---

## Social Security Strategy

Purpose

Document Social Security assumptions.

Tables

* Claiming ages
* Monthly benefit
* Annual benefit
* Spousal benefits
* Survivor benefits

Charts

* Benefit by claiming age

---

## Withdrawal Strategy

Purpose

Describe how retirement assets will be used.

Tables

* Withdrawal order
* Taxable accounts
* Traditional IRA
* Roth IRA
* Cash reserves

Charts

* Withdrawal sources by year

---

# Section 4 – Retirement Spending

## Retirement Budget

Purpose

Summarize expected retirement expenses.

Tables

* Housing
* Utilities
* Food
* Transportation
* Insurance
* Healthcare
* Entertainment
* Travel
* Taxes
* Miscellaneous

Charts

* Spending breakdown

---

## Retirement Spending Model Comparison

Purpose

Compare alternative retirement spending models.

Tables

| Spending Model | Monte Carlo Success | Median Estate | Average Spending | Notes |
| -------------- | ------------------- | ------------- | ---------------- | ----- |

Charts

* Inflation-adjusted spending
* Retirement spending smile

Narrative

Explain the practical differences between the spending models and which is recommended.

---

## Lifetime Cash Flow

Purpose

Illustrate income and expenses throughout retirement.

Tables

Annual summary

* Income
* Spending
* Taxes
* Net cash flow

Charts

* Income vs. expenses
* Annual surplus / deficit

---

# Section 5 – Long-Term Projection

## Lifetime Financial Projection

Purpose

Provide a high-level retirement forecast.

Tables

* Year
* Age
* Income
* Spending
* Taxes
* Ending portfolio

Charts

* Portfolio value over time

---

## Portfolio Growth

Purpose

Illustrate how the portfolio changes over retirement.

Charts

* Portfolio growth
* Annual withdrawals
* Cumulative withdrawals

---

## Estate Projection

Purpose

Estimate long-term legacy.

Tables

Projected estate values at selected ages.

Charts

* Estate value over time

---

# Section 6 – Taxes & Healthcare

## Tax Analysis

Purpose

Estimate retirement tax burden.

Tables

* Federal tax
* State tax
* Effective rate
* Marginal rate
* Capital gains

Charts

* Taxes by year

---

## Healthcare & Medicare

Purpose

Summarize healthcare assumptions.

Tables

* Medicare enrollment
* IRMAA
* Premium estimates
* Long-term care assumptions

Charts

* Healthcare costs over time

---

# Section 7 – Risk Analysis

## Monte Carlo Summary

Purpose

Measure overall retirement success.

Tables

* Success probability
* Median outcome
* Best case
* Worst case
* Failure probability

Charts

* Monte Carlo distribution
* Portfolio percentile curves

---

## Scenario Analysis

Purpose

Stress test the retirement plan.

Example scenarios

* Poor market returns
* High inflation
* Longer life expectancy
* Higher healthcare costs
* Early retirement
* Delayed retirement

Tables

Comparison of success rate under each scenario.

---

## Sensitivity Analysis

Purpose

Show which assumptions have the greatest impact.

Variables

* Retirement age
* Spending
* Inflation
* Investment returns
* Life expectancy

Charts

* Sensitivity (tornado) chart

---

# Section 8 – Action Plan

## Recommended Actions

Purpose

Provide prioritized planning recommendations.

Each recommendation should include

* Description
* Expected benefit
* Priority
* Estimated implementation timeframe

---

## Retirement Timeline

Purpose

Show important future milestones.

Examples

* Retirement
* Social Security
* Medicare
* Pension
* Required Minimum Distributions

Charts

* Retirement timeline

---

# Section 9 – Assumptions & Methodology

## Planning Assumptions

Purpose

Document every assumption used by the engine.

Includes

* Inflation
* Investment returns
* Life expectancy
* Healthcare inflation
* Tax assumptions
* Social Security assumptions

---

## Methodology

Purpose

Increase transparency.

Contents

* Workbook version
* Engine version
* Report generation date
* Calculation methodology
* Data sources
* Limitations

---

# Appendices

## Appendix A – Annual Projection

Detailed year-by-year retirement projection.

Columns

* Year
* Age
* Income
* Spending
* Taxes
* Withdrawals
* Ending portfolio

---

## Appendix B – Account Summary

Every account included in the plan.

---

## Appendix C – Investment Holdings

Detailed list of securities.

---

## Appendix D – Insurance Summary

Insurance policies and coverage.

---

## Appendix E – Workbook Values

Key workbook inputs as interpreted by the engine.

Useful for validation and troubleshooting.

---

# Retirement Spending Models

The retirement spending model determines how retirement expenses evolve over time. This choice affects nearly every downstream calculation, including taxes, withdrawals, portfolio growth, Monte Carlo simulations, and estate projections.

Retirement Engine should treat spending models as first-class planning strategies rather than simple worksheet inputs.

---

## Model 1 – Inflation-Adjusted Spending

### Philosophy

Retirement spending remains constant in real purchasing power.

Every budget category grows annually with inflation.

This is the traditional retirement planning model and provides a conservative baseline.

### Workbook Requirements

Worksheet

```
Retirement Budget - Inflation
```

Suggested columns

* Stable ID
* Category
* Annual Retirement Amount
* Inflation Rule
* Notes

---

## Model 2 – Retirement Spending Smile

### Philosophy

Research has shown that many retirees naturally spend in three broad phases:

1. Go-Go Years
2. Slow-Go Years
3. No-Go Years

Travel and discretionary spending are highest early in retirement, decline during middle retirement, while healthcare often increases later in life.

This model generally reflects observed retiree behavior more accurately than a flat inflation-adjusted budget.

### Workbook Requirements

Worksheet

```
Retirement Budget - Smile
```

Suggested columns

* Stable ID
* Category
* Go-Go Spending
* Slow-Go Spending
* No-Go Spending
* Transition Age 1
* Transition Age 2
* Inflation Rule
* Notes

An alternative implementation may express the later phases as percentages of the initial retirement budget (for example, 100% / 80% / 60%), reducing the amount of data the user must enter.

---

# Reporting Requirements

Whenever multiple spending models are available, the report should evaluate each independently.

The Executive Summary should identify the primary planning model while also presenting a comparison of the alternatives.

Suggested comparison metrics

* Monte Carlo success rate
* Median ending portfolio
* Median estate value
* Worst-case ending balance
* Average annual withdrawals
* Average annual spending
* Lifetime taxes

The Retirement Spending section should include overlay charts comparing projected annual spending under each model, while the Risk Analysis section should compare Monte Carlo results across all supported spending models.

This allows users to understand not only whether their retirement plan succeeds, but also how sensitive that success is to different assumptions about future spending.

---

# Future Spending Models

The architecture should allow additional spending strategies to be added without redesigning the workbook or reporting engine.

Potential future models include

* Dynamic Spending
* Guyton-Klinger Guardrails
* Variable Percentage Withdrawals (VPW)
* Required Spending Only
* User-defined spending curves
* Custom scenario-based spending models

The retirement simulation engine should request annual spending from the selected spending model rather than embedding spending logic directly into the simulation. This separation keeps the engine extensible while allowing future planning strategies to be added with minimal changes.
