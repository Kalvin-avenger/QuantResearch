import pandas as pd

from quantresearch.accounting.option_position import (
    OptionPosition,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.strategy.context import (
    StrategyContext,
)


def test_strategy_context_exposes_option_position():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    position = OptionPosition(
        contract=contract,
        quantity=10,
        average_cost=25.0,
    )

    context = StrategyContext(
        cash=50000.0,
        option_positions={
            contract: position,
        },
    )

    assert context.cash == 50000.0

    assert (
        context.option_positions[contract]
        is position
    )

    assert (
        context.option_positions[contract]
        .average_cost
        == 25.0
    )

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)


def test_strategy_context_exposes_option_quote():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = HistoricalOptionQuote(
        contract=contract,
        timestamp=pd.Timestamp(
            "2026-01-05 15:59:00"
        ),
        bid=32.0,
        ask=33.0,
    )

    context = StrategyContext(
        cash=50000.0,
        option_positions={},
        option_quotes={
            contract: quote,
        },
    )

    assert (
        context.option_quotes[contract].bid
        == 32.0
    )