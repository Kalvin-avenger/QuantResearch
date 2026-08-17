import pandas as pd
import pytest

from quantresearch.backtest.engine import BacktestEngine
from quantresearch.data.historical_option_quote import HistoricalOptionQuote
from quantresearch.data.historical_options import HistoricalOptionQuoteStore
from quantresearch.instruments.options import OptionContract, OptionType
from quantresearch.orders.equity_order_intent import EquityOrderIntent
from quantresearch.orders.option_order_intent import OptionOrderIntent
from quantresearch.portfolio import Portfolio
from quantresearch.signals import Signal

class OneDayMultiInstructionStrategy:

    def __init__(self, contract):
        self.contract = contract

    def generate_orders(
        self,
        prices,
    ):
        return [
            [
                EquityOrderIntent(
                    action=Signal.BUY,
                    allocation_fraction=0.25,
                ),
                OptionOrderIntent(
                    contract=self.contract,
                    action=Signal.BUY,
                    allocation_fraction=0.25,
                ),
            ]
        ]


class MultiInstructionStrategy:

    def __init__(self, contract):
        self.contract = contract

    def generate_orders(self, prices):
        return [
            [
                EquityOrderIntent(
                    action=Signal.BUY,
                    allocation_fraction=0.25,
                ),
                OptionOrderIntent(
                    contract=self.contract,
                    action=Signal.BUY,
                    allocation_fraction=0.25,
                ),
            ],
            None,
        ]


def test_engine_executes_multiple_instructions_same_day():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    prices = pd.Series(
        [500.0, 505.0],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-02 15:59:00"),
            bid=24.5,
            ask=25.5,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-05 15:59:00"),
            bid=25.0,
            ask=26.0,
        ),
    ]

    store = HistoricalOptionQuoteStore.from_historical_quotes(
        quotes
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    strategy = MultiInstructionStrategy(
        contract=contract
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    assert portfolio.position.quantity == 50
    assert contract in portfolio.option_positions
    assert portfolio.option_positions[contract].quantity > 0

    assert len(result.trades) == 1
    assert result.trades[0].quantity == 50

    assert portfolio.cash < 75000.0

def test_multiple_allocations_use_same_day_cash_snapshot():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    prices = pd.Series(
        [500.0],
        index=[
            pd.Timestamp("2026-01-02"),
        ],
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
    ]

    store = (
        HistoricalOptionQuoteStore
        .from_historical_quotes(
            quotes
        )
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    strategy = OneDayMultiInstructionStrategy(
        contract=contract
    )

    engine = BacktestEngine()

    engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    assert portfolio.position.quantity == 50

    option_position = (
        portfolio.option_positions[
            contract
        ]
    )

    assert option_position.quantity == 10

    assert portfolio.cash == pytest.approx(
        50000.0
    )