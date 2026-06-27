from decimal import Decimal

from retirement_engine.calculators import (
    calculate_reserve_row,
    calculate_reserve_rows,
    rollup_reserves,
    total_annual_reserve_contribution,
)
from retirement_engine.config import load_config
from retirement_engine.workbook import load_retirement_workbook
from retirement_engine.workbook.reader import WorkbookRow


def test_calculate_reserve_row_uses_explicit_remaining_life() -> None:
    row = reserve_row(
        row_id="reserve.test.explicit",
        replacement_cost=12000,
        expected_life=10,
        current_age=4,
        remaining_life=3,
        next_year=2029,
    )

    calculated = calculate_reserve_row(row)

    assert calculated.replacement_cost == Decimal(12000)
    assert calculated.expected_useful_life == Decimal(10)
    assert calculated.current_age == Decimal(4)
    assert calculated.remaining_useful_life == Decimal(3)
    assert calculated.next_replacement_year == 2029
    assert calculated.annual_contribution == Decimal(4000)
    assert calculated.monthly_contribution == Decimal("333.3333333333333333333333333")
    assert calculated.has_amount is True


def test_calculate_reserve_row_falls_back_to_expected_life_minus_current_age() -> None:
    row = reserve_row(
        row_id="reserve.test.fallback",
        replacement_cost=9000,
        expected_life=12,
        current_age=3,
        remaining_life=None,
        next_year=2035,
    )

    calculated = calculate_reserve_row(row)

    assert calculated.remaining_useful_life == Decimal(9)
    assert calculated.annual_contribution == Decimal(1000)
    assert calculated.monthly_contribution == Decimal("83.33333333333333333333333333")


def test_calculate_reserve_row_without_remaining_life_has_zero_contribution() -> None:
    row = reserve_row(
        row_id="reserve.test.expired",
        replacement_cost=5000,
        expected_life=5,
        current_age=5,
        remaining_life=None,
        next_year=None,
    )

    calculated = calculate_reserve_row(row)

    assert calculated.remaining_useful_life == Decimal(0)
    assert calculated.annual_contribution == Decimal(0)
    assert calculated.monthly_contribution == Decimal(0)
    assert calculated.next_replacement_year is None


def test_rollup_reserves() -> None:
    rows = calculate_reserve_rows(
        (
            reserve_row(
                row_id="reserve.test.one",
                replacement_cost=12000,
                expected_life=10,
                current_age=0,
                remaining_life=4,
                next_year=2030,
            ),
            reserve_row(
                row_id="reserve.test.two",
                replacement_cost=6000,
                expected_life=6,
                current_age=0,
                remaining_life=3,
                next_year=2029,
            ),
            reserve_row(
                row_id="reserve.test.blank",
                replacement_cost=None,
                expected_life=None,
                current_age=None,
                remaining_life=None,
                next_year=None,
            ),
        )
    )

    rollup = rollup_reserves(rows)

    assert rollup.item_count == 2
    assert rollup.annual_contribution == Decimal(5000)
    assert rollup.monthly_contribution == Decimal("416.6666666666666666666666667")


def test_calculate_example_reserve_total() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    calculated_rows = calculate_reserve_rows(workbook.sheet("Reserves").rows)
    rollup = rollup_reserves(calculated_rows)

    assert rollup.item_count == 22
    assert round(total_annual_reserve_contribution(calculated_rows)) == Decimal(55265)
    assert round(rollup.monthly_contribution) == Decimal(4605)


def reserve_row(
    *,
    row_id: str,
    replacement_cost: int | None,
    expected_life: int | None,
    current_age: int | None,
    remaining_life: int | None,
    next_year: int | None,
) -> WorkbookRow:
    return WorkbookRow(
        row_number=2,
        values={
            "Reserve Item": "Example",
            "Estimated Replacement Cost": replacement_cost,
            "Expected Useful Life": expected_life,
            "Current Age": current_age,
            "Remaining Useful Life": remaining_life,
            "Next Replacement Year": next_year,
            "Notes": None,
            "ID": row_id,
        },
    )
