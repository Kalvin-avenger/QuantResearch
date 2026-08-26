import pandas as pd

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

from quantresearch.data.historical_option_bar import (
    HistoricalOptionBar
)

from quantresearch.portfolio import Portfolio
from quantresearch.backtest.engine import BacktestEngine
from quantresearch.signals import Signal

from quantresearch.orders.option_order import (
    OptionOrder,
)

from quantresearch.data.daily_option_pricing import (
    DailyCloseOptionPricingPolicy,
    DailyOptionPricing
)

from quantresearch.accounting.option_position import (
    OptionContract,
    OptionPosition,
)




def test_execute_explicit_option_order_supports_daily_option_bar_provider():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    bar = HistoricalOptionBar(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        open=28.0,
        high=31.0,
        low=27.5,
        close=30.0,
        volume=1250.0,
        vwap=29.4,
    )

    class FakeOptionBarProvider:
        def __init__(self):
            self.calls = []

        def get_bar(
            self,
            timestamp,
            contract,
        ):
            self.calls.append(
                (timestamp, contract)
            )

            return bar

    provider = FakeOptionBarProvider()

    portfolio = Portfolio(
        initial_cash=100000,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.BUY,
        quantity=1,
    )

    engine = BacktestEngine()

    engine._execute_explicit_instruction(
        instruction=order,
        price=500.0,
        timestamp=pd.Timestamp("2026-01-02"),
        portfolio=portfolio,
        trades=[],
        option_data_provider=None,
        option_bar_provider=provider,
        option_pricing_policy=DailyCloseOptionPricingPolicy(),
        allocation_cash=100000,
    )

    assert len(provider.calls) == 1

    assert provider.calls[0] == (
        pd.Timestamp("2026-01-02"),
        contract,
    )

    assert contract in portfolio.option_positions

    position = portfolio.option_positions[contract]

    assert position.quantity == 1
    assert position.average_cost == 30.0

    assert portfolio.cash == 97000.0

def test_execute_explicit_option_sell_uses_daily_sell_price():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    class FakePricingPolicy:
        def get_pricing(self, bar):
            return DailyOptionPricing(
                contract=bar.contract,
                timestamp=bar.timestamp,
                buy_price=30.0,
                sell_price=29.5,
                mark_price=29.75,
            )

    bar = HistoricalOptionBar(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        open=28.0,
        high=31.0,
        low=27.5,
        close=30.0,
        volume=1250.0,
        vwap=29.4,
    )

    class FakeOptionBarProvider:
        def get_bar(
            self,
            timestamp,
            contract,
        ):
            return bar

    portfolio = Portfolio(
        initial_cash=100000,
    )

    portfolio.option_positions[contract] = OptionPosition(
        contract=contract,
        quantity=1,
        average_cost=25.0,
    )

    order = OptionOrder(
        contract=contract,
        action=Signal.SELL,
        quantity=1,
    )

    engine = BacktestEngine()

    engine._execute_explicit_instruction(
        instruction=order,
        price=500.0,
        timestamp=pd.Timestamp("2026-01-02"),
        portfolio=portfolio,
        trades=[],
        option_data_provider=None,
        option_bar_provider=FakeOptionBarProvider(),
        option_pricing_policy=FakePricingPolicy(),
        allocation_cash=100000,
    )

    assert contract not in portfolio.option_positions

    assert portfolio.cash == 102950.0