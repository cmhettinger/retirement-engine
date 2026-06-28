from decimal import Decimal

from retirement_engine.analysis import estimate_retirement_readiness
from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook


def test_estimate_retirement_readiness_projects_assets_and_required_need() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    estimate = estimate_retirement_readiness(workbook)

    assert estimate.status == "on_track"
    assert estimate.years_until_retirement == 9
    assert estimate.planning_horizon_years == 35
    assert estimate.expected_investment_return == Decimal("0.055")
    assert estimate.inflation_rate == Decimal("0.03")
    assert estimate.real_return_rate == Decimal("0.024271844660194174757281553")

    assert estimate.current_retirement_assets == Decimal(1706000)
    assert estimate.annual_retirement_contributions == Decimal(84800)
    assert estimate.projected_retirement_assets == Decimal("3716705.637151269525948058594")
    assert estimate.required_retirement_assets == Decimal("1344151.683306994144813389314")
    assert estimate.surplus_or_shortfall == Decimal("2372553.953844275381134669280")
    assert estimate.funded_ratio == Decimal("2.765093912620873372751864445")

    assert estimate.annual_spending_need == Decimal("238931.1443001443001443001443")
    assert estimate.annual_retirement_income == Decimal(194100)
    assert estimate.annual_withdrawal_need == Decimal("44831.1443001443001443001443")
    assert estimate.desired_cash_reserve == Decimal(45000)
    assert estimate.desired_estate_value == Decimal(250000)


def test_retirement_readiness_estimate_serializes_to_grouped_dict() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    estimate = estimate_retirement_readiness(workbook)

    assert estimate.to_dict()["timeline"] == {
        "years_until_retirement": 9,
        "planning_horizon_years": 35,
    }
    assert estimate.to_dict()["assets"] == {
        "current_retirement_assets": Decimal(1706000),
        "annual_retirement_contributions": Decimal(84800),
        "projected_retirement_assets": Decimal("3716705.637151269525948058594"),
        "required_retirement_assets": Decimal("1344151.683306994144813389314"),
        "desired_cash_reserve": Decimal(45000),
        "desired_estate_value": Decimal(250000),
        "surplus_or_shortfall": Decimal("2372553.953844275381134669280"),
        "funded_ratio": Decimal("2.765093912620873372751864445"),
    }
    assert estimate.to_dict()["cash_flow"] == {
        "annual_spending_need": Decimal("238931.1443001443001443001443"),
        "annual_retirement_income": Decimal(194100),
        "annual_withdrawal_need": Decimal("44831.1443001443001443001443"),
    }
