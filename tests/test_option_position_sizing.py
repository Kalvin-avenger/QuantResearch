from quantresearch.strategy.position_sizing import (
    calculate_option_quantity,
)


def test_calculate_option_quantity_uses_allocation_fraction():

    quantity = calculate_option_quantity(
        cash=100_000,
        option_price=51.0,
        multiplier=100,
        allocation_fraction=0.25,
    )

    assert quantity == 4

import pytest

from quantresearch.strategy.position_sizing import (
    calculate_option_quantity,
)


def test_calculate_option_quantity_returns_zero_when_budget_is_insufficient():

    quantity = calculate_option_quantity(
        cash=10_000,
        option_price=51.0,
        multiplier=100,
        allocation_fraction=0.25,
    )

    assert quantity == 0


def test_calculate_option_quantity_rejects_non_positive_option_price():

    with pytest.raises(
        ValueError,
        match="option_price must be positive",
    ):
        calculate_option_quantity(
            cash=100_000,
            option_price=0.0,
            multiplier=100,
            allocation_fraction=0.25,
        )


def test_calculate_option_quantity_rejects_invalid_allocation_fraction():

    with pytest.raises(
        ValueError,
        match="allocation_fraction must be greater than 0 and at most 1",
    ):
        calculate_option_quantity(
            cash=100_000,
            option_price=51.0,
            multiplier=100,
            allocation_fraction=0.0,
        )

    with pytest.raises(
        ValueError,
        match="allocation_fraction must be greater than 0 and at most 1",
    ):
        calculate_option_quantity(
            cash=100_000,
            option_price=51.0,
            multiplier=100,
            allocation_fraction=1.1,
        )


def test_calculate_option_quantity_rejects_non_positive_multiplier():

    with pytest.raises(
        ValueError,
        match="multiplier must be positive",
    ):
        calculate_option_quantity(
            cash=100_000,
            option_price=51.0,
            multiplier=0,
            allocation_fraction=0.25,
        )