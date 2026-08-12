import pandas as pd

from quantresearch.backtest.engine import BacktestEngine
from quantresearch.data.historical_options import (
    HistoricalOptionDataProvider,
    HistoricalOptionQuote,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.portfolio.portfolio import Portfolio
from quantresearch.strategy.buy_and_hold_option import (
    BuyAndHoldOptionStrategy,
)


class FakeHistoricalOptionDataProvider(
    HistoricalOptionDataProvider
):

    def __init__(
        self,
        quotes,
    ):
        self.quotes = quotes

    def get_quote(
        self,
        timestamp,
        contract,
    ):

        timestamp = pd.Timestamp(timestamp)

        return self.quotes[timestamp]


def test_buy_and_hold_option_strategy_creates_option_position():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quotes = {
        pd.Timestamp("2026-01-02"):
            HistoricalOptionQuote(
                contract=contract,
                timestamp=pd.Timestamp(
                    "2026-01-02 15:59:00"
                ),
                bid=49.0,
                ask=51.0,
            ),

        pd.Timestamp("2026-01-05"):
            HistoricalOptionQuote(
                contract=contract,
                timestamp=pd.Timestamp(
                    "2026-01-05 15:59:00"
                ),
                bid=61.0,
                ask=63.0,
            ),
    }

    provider = FakeHistoricalOptionDataProvider(
        quotes=quotes
    )

    strategy = BuyAndHoldOptionStrategy(
        contract=contract,
        quantity=1,
    )

    prices = pd.Series(
        [500.0, 510.0, 520.0],
        index=pd.to_datetime(
            [
                "2026-01-02",
                "2026-01-05",
                "2026-01-06",
            ]
        ),
    )

    portfolio = Portfolio(
        initial_cash=100_000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=provider,
    )

    assert contract in result.portfolio.option_positions

    position = result.portfolio.option_positions[
        contract
    ]

    assert position.quantity == 1
    assert result.portfolio.cash == 94_900
    assert position.average_cost == 51.0

import pandas as pd

from quantresearch.data.historical_options import (
    HistoricalOptionQuote,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.orders.option_order import OptionOrder
from quantresearch.signals import Signal
from quantresearch.portfolio.portfolio import Portfolio
from quantresearch.backtest.engine import BacktestEngine


class BuyThenSellOptionStrategy:

    def __init__(
        self,
        contract,
    ):
        self.contract = contract

    def generate_orders(
        self,
        prices,
    ):
        return [
            OptionOrder(
                contract=self.contract,
                action=Signal.BUY,
                quantity=1,
            ),
            OptionOrder(
                contract=self.contract,
                action=Signal.SELL,
                quantity=1,
            ),
        ]


def test_option_backtest_buy_then_sell_realizes_profit():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quotes = {
        pd.Timestamp("2026-01-02"):
            HistoricalOptionQuote(
                contract=contract,
                timestamp=pd.Timestamp(
                    "2026-01-02 15:59:00"
                ),
                bid=49.0,
                ask=51.0,
            ),

        pd.Timestamp("2026-01-05"):
            HistoricalOptionQuote(
                contract=contract,
                timestamp=pd.Timestamp(
                    "2026-01-05 15:59:00"
                ),
                bid=61.0,
                ask=63.0,
            ),
    }

    provider = FakeHistoricalOptionDataProvider(
        quotes=quotes
    )

    strategy = BuyThenSellOptionStrategy(
        contract=contract
    )

    prices = pd.Series(
        [500.0, 510.0],
        index=pd.to_datetime(
            [
                "2026-01-02",
                "2026-01-05",
            ]
        ),
    )

    portfolio = Portfolio(
        initial_cash=100_000
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=provider,
    )

    assert contract not in result.portfolio.option_positions
    assert result.portfolio.realized_pnl == 1_000
    assert result.portfolio.cash == 101_000