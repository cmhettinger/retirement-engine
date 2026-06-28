from decimal import Decimal

from retirement_engine.config import load_config
from retirement_engine.projections import project_retirement_years
from retirement_engine.workbook import load_retirement_workbook


def test_project_retirement_years_builds_annual_projection() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    projection = project_retirement_years(workbook, start_year=2026)

    assert projection.start_year == 2026
    assert projection.retirement_year == 2035
    assert projection.years_until_retirement == 9
    assert projection.planning_horizon_years == 35
    assert projection.expected_investment_return == Decimal("0.055")
    assert projection.inflation_rate == Decimal("0.03")
    assert projection.current_retirement_assets == Decimal(1706000)
    assert projection.annual_retirement_contributions == Decimal(84800)
    assert projection.depletion_year is None
    assert len(projection.rows) == 35


def test_project_retirement_years_tracks_pre_retirement_and_retirement_cash_flow() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    projection = project_retirement_years(workbook, start_year=2026)

    first_year = projection.rows[0]
    assert first_year.year_index == 1
    assert first_year.calendar_year == 2027
    assert first_year.person1_age == 59
    assert first_year.person2_age == 57
    assert first_year.is_retirement_year is False
    assert first_year.is_retired is False
    assert first_year.starting_portfolio == Decimal(1706000)
    assert first_year.contributions == Decimal(84800)
    assert first_year.investment_return == Decimal("93830.000")
    assert first_year.annual_expenses == Decimal("246099.0786291486291486291486")
    assert first_year.annual_income == Decimal("199923.00")
    assert first_year.withdrawal == Decimal(0)
    assert first_year.ending_portfolio == Decimal("1884630.000")

    retirement_year = projection.rows[8]
    assert retirement_year.calendar_year == 2035
    assert retirement_year.person1_age == 67
    assert retirement_year.person2_age == 65
    assert retirement_year.is_retirement_year is True
    assert retirement_year.is_retired is False
    assert retirement_year.contributions == Decimal(84800)
    assert retirement_year.withdrawal == Decimal(0)
    assert retirement_year.ending_portfolio == Decimal("3716705.637151269525948058594")

    first_retired_year = projection.rows[9]
    assert first_retired_year.calendar_year == 2036
    assert first_retired_year.is_retirement_year is False
    assert first_retired_year.is_retired is True
    assert first_retired_year.contributions == Decimal(0)
    assert first_retired_year.withdrawal == Decimal("60249.3091297037965017470010")
    assert first_retired_year.ending_portfolio == Decimal("3860875.138064885553373454816")


def test_annual_projection_serializes_to_dict() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    projection = project_retirement_years(workbook, start_year=2026)

    projection_dict = projection.to_dict()
    rows = projection_dict["rows"]
    assert isinstance(rows, list)
    assert projection_dict["retirement_year"] == 2035
    assert projection_dict["depletion_year"] is None
    assert rows[0] == {
        "year_index": 1,
        "calendar_year": 2027,
        "person1_age": 59,
        "person2_age": 57,
        "is_retirement_year": False,
        "is_retired": False,
        "starting_portfolio": Decimal(1706000),
        "contributions": Decimal(84800),
        "investment_return": Decimal("93830.000"),
        "annual_expenses": Decimal("246099.0786291486291486291486"),
        "annual_income": Decimal("199923.00"),
        "withdrawal": Decimal(0),
        "ending_portfolio": Decimal("1884630.000"),
    }
