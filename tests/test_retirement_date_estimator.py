from decimal import Decimal

from retirement_engine.config import load_config
from retirement_engine.projections import estimate_retirement_dates, project_retirement_years
from retirement_engine.workbook import load_retirement_workbook


def test_estimate_retirement_dates_finds_earliest_viable_candidate() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    estimate = estimate_retirement_dates(workbook, start_year=2026)

    assert estimate.start_year == 2026
    assert estimate.planned_retirement_year == 2035
    assert estimate.planned_years_until_retirement == 9
    assert estimate.earliest_viable_retirement_year == 2026
    assert estimate.earliest_viable_years_until_retirement == 0
    assert len(estimate.candidates) == 36

    immediate = estimate.candidates[0]
    assert immediate.years_until_retirement == 0
    assert immediate.retirement_year == 2026
    assert immediate.person1_retirement_age == 58
    assert immediate.person2_retirement_age == 56
    assert immediate.viable is True
    assert immediate.depletion_year is None
    assert immediate.ending_portfolio == Decimal("4278594.991622544215112399861")
    assert immediate.minimum_required_ending_portfolio == Decimal(295000)
    assert immediate.surplus_or_shortfall == Decimal("3983594.991622544215112399861")


def test_estimate_retirement_dates_includes_planned_retirement_candidate() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    estimate = estimate_retirement_dates(workbook, start_year=2026)

    planned = estimate.candidates[estimate.planned_years_until_retirement]
    assert planned.years_until_retirement == 9
    assert planned.retirement_year == 2035
    assert planned.person1_retirement_age == 67
    assert planned.person2_retirement_age == 65
    assert planned.viable is True
    assert planned.depletion_year is None
    assert planned.ending_portfolio == Decimal("10454481.78513387464896033967")
    assert planned.surplus_or_shortfall == Decimal("10159481.78513387464896033967")


def test_retirement_date_estimate_serializes_to_dict() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    estimate = estimate_retirement_dates(workbook, start_year=2026)

    estimate_dict = estimate.to_dict()
    candidates = estimate_dict["candidates"]
    assert isinstance(candidates, list)
    assert estimate_dict["planned_retirement_year"] == 2035
    assert estimate_dict["earliest_viable_retirement_year"] == 2026
    assert candidates[0] == {
        "years_until_retirement": 0,
        "retirement_year": 2026,
        "person1_retirement_age": 58,
        "person2_retirement_age": 56,
        "viable": True,
        "depletion_year": None,
        "ending_portfolio": Decimal("4278594.991622544215112399861"),
        "minimum_required_ending_portfolio": Decimal(295000),
        "surplus_or_shortfall": Decimal("3983594.991622544215112399861"),
    }


def test_projection_engine_accepts_retirement_year_override() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    projection = project_retirement_years(
        workbook,
        start_year=2026,
        retirement_years_from_start=0,
    )

    assert projection.retirement_year == 2026
    assert projection.years_until_retirement == 0
    assert projection.rows[0].is_retired is True
    assert projection.rows[0].contributions == Decimal(0)
    assert projection.rows[0].withdrawal == Decimal("46176.0786291486291486291486")
