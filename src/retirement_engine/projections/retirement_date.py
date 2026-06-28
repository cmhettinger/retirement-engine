"""Retirement date estimator built from annual projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from retirement_engine.projections.annual import project_retirement_years
from retirement_engine.workbook.reader import RetirementWorkbook, WorkbookCellValue, WorkbookRow


@dataclass(frozen=True)
class RetirementDateCandidate:
    years_until_retirement: int
    retirement_year: int
    person1_retirement_age: int
    person2_retirement_age: int
    viable: bool
    depletion_year: int | None
    ending_portfolio: Decimal
    minimum_required_ending_portfolio: Decimal
    surplus_or_shortfall: Decimal

    def to_dict(self) -> dict[str, object]:
        return {
            "years_until_retirement": self.years_until_retirement,
            "retirement_year": self.retirement_year,
            "person1_retirement_age": self.person1_retirement_age,
            "person2_retirement_age": self.person2_retirement_age,
            "viable": self.viable,
            "depletion_year": self.depletion_year,
            "ending_portfolio": self.ending_portfolio,
            "minimum_required_ending_portfolio": self.minimum_required_ending_portfolio,
            "surplus_or_shortfall": self.surplus_or_shortfall,
        }


@dataclass(frozen=True)
class RetirementDateEstimate:
    start_year: int
    planned_retirement_year: int
    planned_years_until_retirement: int
    earliest_viable_retirement_year: int | None
    earliest_viable_years_until_retirement: int | None
    candidates: tuple[RetirementDateCandidate, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "start_year": self.start_year,
            "planned_retirement_year": self.planned_retirement_year,
            "planned_years_until_retirement": self.planned_years_until_retirement,
            "earliest_viable_retirement_year": self.earliest_viable_retirement_year,
            "earliest_viable_years_until_retirement": self.earliest_viable_years_until_retirement,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


def estimate_retirement_dates(
    workbook: RetirementWorkbook,
    *,
    start_year: int | None = None,
) -> RetirementDateEstimate:
    """Evaluate potential retirement years against the annual projection model."""

    assumptions = workbook.sheet("Assumptions").rows_by_id
    projection_start_year = start_year if start_year is not None else date.today().year
    person1_current_age = int(_assumption_decimal(assumptions, "assumptions.person1.current_age"))
    person2_current_age = int(_assumption_decimal(assumptions, "assumptions.person2.current_age"))
    planned_years_until_retirement = _years_until_retirement(assumptions)
    planning_horizon_years = int(
        _assumption_decimal(assumptions, "assumptions.household.planning_horizon_years")
    )
    minimum_required_ending_portfolio = _assumption_decimal(
        assumptions,
        "assumptions.household.desired_cash_reserve",
    ) + _assumption_decimal(assumptions, "assumptions.household.desired_estate_value")

    candidates = tuple(
        _candidate(
            workbook=workbook,
            start_year=projection_start_year,
            years_until_retirement=years_until_retirement,
            person1_current_age=person1_current_age,
            person2_current_age=person2_current_age,
            minimum_required_ending_portfolio=minimum_required_ending_portfolio,
        )
        for years_until_retirement in range(0, planning_horizon_years + 1)
    )
    earliest_viable = next((candidate for candidate in candidates if candidate.viable), None)

    return RetirementDateEstimate(
        start_year=projection_start_year,
        planned_retirement_year=projection_start_year + planned_years_until_retirement,
        planned_years_until_retirement=planned_years_until_retirement,
        earliest_viable_retirement_year=(
            earliest_viable.retirement_year if earliest_viable is not None else None
        ),
        earliest_viable_years_until_retirement=(
            earliest_viable.years_until_retirement if earliest_viable is not None else None
        ),
        candidates=candidates,
    )


def _candidate(
    *,
    workbook: RetirementWorkbook,
    start_year: int,
    years_until_retirement: int,
    person1_current_age: int,
    person2_current_age: int,
    minimum_required_ending_portfolio: Decimal,
) -> RetirementDateCandidate:
    projection = project_retirement_years(
        workbook,
        start_year=start_year,
        retirement_years_from_start=years_until_retirement,
    )
    ending_portfolio = projection.rows[-1].ending_portfolio if projection.rows else Decimal(0)
    surplus_or_shortfall = ending_portfolio - minimum_required_ending_portfolio
    viable = projection.depletion_year is None and surplus_or_shortfall >= 0

    return RetirementDateCandidate(
        years_until_retirement=years_until_retirement,
        retirement_year=start_year + years_until_retirement,
        person1_retirement_age=person1_current_age + years_until_retirement,
        person2_retirement_age=person2_current_age + years_until_retirement,
        viable=viable,
        depletion_year=projection.depletion_year,
        ending_portfolio=ending_portfolio,
        minimum_required_ending_portfolio=minimum_required_ending_portfolio,
        surplus_or_shortfall=surplus_or_shortfall,
    )


def _years_until_retirement(assumptions: Mapping[str, WorkbookRow]) -> int:
    years = []
    for person in ("person1", "person2"):
        current_age = _assumption_decimal(assumptions, f"assumptions.{person}.current_age")
        retirement_age = _assumption_decimal(
            assumptions,
            f"assumptions.{person}.planned_retirement_age",
        )
        years.append(max(int(retirement_age - current_age), 0))
    return min(years)


def _assumption_decimal(assumptions: Mapping[str, WorkbookRow], row_id: str) -> Decimal:
    return _number(assumptions[row_id].values.get("Value"))


def _number(value: WorkbookCellValue) -> Decimal:
    if isinstance(value, bool) or value is None:
        return Decimal(0)
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str) and value.strip():
        return Decimal(value.strip())
    return Decimal(0)
