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