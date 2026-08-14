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
from quantresearch.orders.option_order import OptionOrder
from quantresearch.portfolio.portfolio import Portfolio
from quantresearch.signals import Signal


class FakeHistoricalOptionDataProvider(
    HistoricalOptionDataProvider
):

    def __init__(
        self,
        quote: HistoricalOptionQuote,
    ):
        self.quote = quote
        self.calls = []

    def get_quote(
        self,
        timestamp,
        contract: OptionContract,
    ) -> HistoricalOptionQuote:

        self.calls.append(
            {
                "timestamp": pd.Timestamp(timestamp),
                "contract": contract,
            }
        )

        return self.quote


class FakeOptionStrategy:

    def __init__(
        self,
        orders,
    ):
        self.orders = orders

    def generate_orders(
        self,
        prices: pd.Series,
    ):
        return self.orders


def test_engine_executes_option_order_using_historical_provider():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = HistoricalOptionQuote(
        contract=contract,
        timestamp=pd.Timestamp(
            "2026-01-02 15:59:00"
        ),
        bid=49.0,
        ask=51.0,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=1,
    )

    provider = FakeHistoricalOptionDataProvider(
        quote=quote
    )

    strategy = FakeOptionStrategy(
        orders=[
            order,
        ]
    )

    prices = pd.Series(
        [500.0],
        index=[
            pd.Timestamp(
                "2026-01-02"
            )
        ],
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

    assert len(provider.calls) == 2

    assert (
        provider.calls[0]["timestamp"]
        == pd.Timestamp("2026-01-02")
    )

    assert (
        provider.calls[1]["timestamp"]
        == pd.Timestamp("2026-01-02")
    )

    assert (
        provider.calls[0]["contract"]
        == contract
    )

    assert (
        provider.calls[1]["contract"]
        == contract
    )
    assert result.portfolio is portfolio