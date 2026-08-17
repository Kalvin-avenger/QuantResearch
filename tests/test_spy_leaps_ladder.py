import pandas as pd
import pytest

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.strategy.spy_leaps_ladder import (
    SpyLeapsLadderStrategy,
)


def test_spy_leaps_ladder_initial_allocations():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    assert strategy.equity_allocation == pytest.approx(
        0.25
    )

    assert strategy.option_allocation == pytest.approx(
        0.25
    )

    assert strategy.leaps_contract == contract

def test_spy_leaps_ladder_generates_initial_orders():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    instructions = strategy.generate_initial_instructions()

    assert len(instructions) == 2

    equity_instruction = instructions[0]
    option_instruction = instructions[1]

    assert equity_instruction.allocation_fraction == pytest.approx(
        0.25
    )

    assert option_instruction.allocation_fraction == pytest.approx(
        0.25
    )

    assert option_instruction.contract == contract

def test_spy_leaps_ladder_calculates_drawdown():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    drawdown = strategy.calculate_drawdown(
        price=475.0,
        peak_price=500.0,
    )

    assert drawdown == pytest.approx(
        -0.05
    )

@pytest.mark.parametrize(
    "price, expected_level",
    [
        (500.0, 0),
        (490.0, 0),
        (475.0, 1),
        (460.0, 1),
        (450.0, 2),
        (425.0, 3),
    ],
)
def test_spy_leaps_ladder_drawdown_levels(
    price,
    expected_level,
):

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    level = strategy.drawdown_level(
        price=price,
        peak_price=500.0,
    )

    assert level == expected_level

def test_drawdown_level_triggers_only_once():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    prices = [
        500.0,
        480.0,
        475.0,
        470.0,
        455.0,
        450.0,
        460.0,
    ]

    triggers = [
        strategy.update_drawdown_state(price)
        for price in prices
    ]

    assert triggers == [
        None,
        None,
        1,
        None,
        None,
        2,
        None,
    ]

def test_new_peak_resets_drawdown_ladder():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    assert strategy.update_drawdown_state(
        500.0
    ) is None

    assert strategy.update_drawdown_state(
        475.0
    ) == 1

    assert strategy.update_drawdown_state(
        510.0
    ) is None

    assert strategy.peak_price == pytest.approx(
        510.0
    )

    assert strategy.last_triggered_level == 0

    assert strategy.update_drawdown_state(
        484.5
    ) == 1

def test_generate_orders_adds_tranche_on_drawdown_levels():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    prices = pd.Series(
        [
            500.0,
            480.0,
            475.0,
            470.0,
            450.0,
        ],
        index=pd.date_range(
            "2026-01-02",
            periods=5,
            freq="B",
        ),
    )

    orders = strategy.generate_orders(
        prices
    )

    assert orders[0] is not None
    assert orders[1] is None
    assert orders[2] is not None
    assert orders[3] is None
    assert orders[4] is not None

    assert len(orders[0]) == 2
    assert len(orders[2]) == 2
    assert len(orders[4]) == 2

def test_drawdown_tranches_use_configured_allocations():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    prices = pd.Series(
        [
            500.0,
            475.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    orders = strategy.generate_orders(
        prices
    )

    drawdown_orders = orders[1]

    equity_intent = drawdown_orders[0]
    option_intent = drawdown_orders[1]

    assert equity_intent.allocation_fraction == pytest.approx(
        0.20
    )

    assert option_intent.allocation_fraction == pytest.approx(
        0.15
    )

def test_ladder_tranches_use_fixed_initial_capital():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    prices = pd.Series(
        [
            500.0,
            475.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    orders = strategy.generate_orders(
        prices
    )

    initial_orders = orders[0]
    drawdown_orders = orders[1]

    assert initial_orders[0].allocation_base == pytest.approx(
        100000.0
    )
    assert initial_orders[1].allocation_base == pytest.approx(
        100000.0
    )

    assert drawdown_orders[0].allocation_base == pytest.approx(
        100000.0
    )
    assert drawdown_orders[1].allocation_base == pytest.approx(
        100000.0
    )

def test_ladder_respects_max_tranches():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        initial_capital=100000.0,
        max_tranches=3,
    )

    prices = pd.Series(
        [
            500.0,
            475.0,
            450.0,
            425.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
            pd.Timestamp("2026-01-07"),
        ],
    )

    orders = strategy.generate_orders(
        prices
    )

    assert orders[0] is not None
    assert orders[1] is not None

    assert orders[2] is None
    assert orders[3] is None

    assert strategy.tranches_deployed == 2

def test_ladder_can_support_more_tranches_when_configured():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    prices = pd.Series(
        [
            500.0,
            475.0,
            450.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
        ],
    )

    orders = strategy.generate_orders(
        prices
    )

    assert orders[0] is not None
    assert orders[1] is not None
    assert orders[2] is not None

    assert strategy.tranches_deployed == 3