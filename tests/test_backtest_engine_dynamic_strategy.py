import pandas as pd
import pytest

from quantresearch.backtest.engine import BacktestEngine
from quantresearch.orders.equity_order_intent import EquityOrderIntent
from quantresearch.portfolio import Portfolio
from quantresearch.signals import Signal

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

from quantresearch.orders.option_order import (
    OptionOrder,
)

from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)

from quantresearch.data.historical_options import (
    HistoricalOptionQuoteStore,
)

from quantresearch.data.daily_option_pricing import (
    DailyCloseOptionPricingPolicy,
)

from quantresearch.data.historical_option_bar import (
    HistoricalOptionBar,
)

from quantresearch.accounting.option_position import OptionPosition


class DynamicStrategy:

    def __init__(self):
        self.contexts = []

    def on_bar(
        self,
        timestamp,
        price,
        context,
    ):
        self.contexts.append(context)

        if len(self.contexts) == 1:
            return EquityOrderIntent(
                action=Signal.BUY,
                allocation_fraction=0.25,
            )

        return None


def test_engine_supports_dynamic_on_bar_strategy():

    prices = pd.Series(
        [500.0, 510.0],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    strategy = DynamicStrategy()

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
    )

    assert portfolio.position.quantity == 50

    assert portfolio.cash == pytest.approx(
        75000.0
    )

    assert len(strategy.contexts) == 2

    assert strategy.contexts[0].cash == pytest.approx(
        100000.0
    )

    assert strategy.contexts[1].cash == pytest.approx(
        75000.0
    )

    assert len(result.trades) == 1

def test_engine_dynamic_strategy_supports_multiple_instructions_on_same_bar():

    prices = pd.Series(
        [100.0],
        index=[
            pd.Timestamp("2026-01-02"),
        ],
    )

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    class MultiInstructionStrategy:

        def on_bar(
            self,
            timestamp,
            price,
            context,
        ):

            return [
                EquityOrderIntent(
                    action=Signal.BUY,
                    allocation_fraction=0.25,
                    allocation_base=100000.0,
                ),
                EquityOrderIntent(
                    action=Signal.BUY,
                    allocation_fraction=0.25,
                    allocation_base=100000.0,
                ),
            ]

    strategy = MultiInstructionStrategy()

    engine = BacktestEngine()

    engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
    )

    assert (
        portfolio.position.quantity
        == 500
    )

    assert portfolio.cash == pytest.approx(
        50000.0
    )

def test_engine_executes_multiple_option_sells_on_same_bar():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-01-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    # =====================================================
    # Two trading days
    # =====================================================

    prices = pd.Series(
        [
            500.0,
            510.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    # =====================================================
    # Contract A:
    #
    # Buy at ask 25
    # Sell at bid 30
    # =====================================================

    # =====================================================
    # Contract B:
    #
    # Buy at ask 25
    # Sell at bid 40
    # =====================================================

    quotes = [
        HistoricalOptionQuote(
            contract=contract_a,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
        HistoricalOptionQuote(
            contract=contract_a,
            timestamp=pd.Timestamp(
                "2026-01-05 15:59:00"
            ),
            bid=30.0,
            ask=31.0,
        ),
        HistoricalOptionQuote(
            contract=contract_b,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
        HistoricalOptionQuote(
            contract=contract_b,
            timestamp=pd.Timestamp(
                "2026-01-05 15:59:00"
            ),
            bid=40.0,
            ask=41.0,
        ),
    ]

    store = (
        HistoricalOptionQuoteStore
        .from_historical_quotes(
            quotes
        )
    )

    # =====================================================
    # Dynamic strategy
    # =====================================================

    class MultiOptionStrategy:

        def __init__(self):
            self.bar_count = 0

        def on_bar(
            self,
            timestamp,
            price,
            context,
        ):

            self.bar_count += 1

            # ---------------------------------------------
            # Day 1:
            # Buy 25% allocation in each option.
            # ---------------------------------------------

            if self.bar_count == 1:

                return [
                    OptionOrderIntent(
                        contract=contract_a,
                        action=Signal.BUY,
                        allocation_fraction=0.25,
                        allocation_base=100000.0,
                    ),
                    OptionOrderIntent(
                        contract=contract_b,
                        action=Signal.BUY,
                        allocation_fraction=0.25,
                        allocation_base=100000.0,
                    ),
                ]

            # ---------------------------------------------
            # Day 2:
            # Sell both positions on the same bar.
            # ---------------------------------------------

            position_a = (
                context.option_positions[
                    contract_a
                ]
            )

            position_b = (
                context.option_positions[
                    contract_b
                ]
            )

            return [
                OptionOrder(
                    contract=contract_a,
                    action=Signal.SELL,
                    quantity=position_a.quantity,
                ),
                OptionOrder(
                    contract=contract_b,
                    action=Signal.SELL,
                    quantity=position_b.quantity,
                ),
            ]

    strategy = MultiOptionStrategy()

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    engine = BacktestEngine()

    engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    # =====================================================
    # Both option positions must be gone.
    # =====================================================

    assert contract_a not in (
        portfolio.option_positions
    )

    assert contract_b not in (
        portfolio.option_positions
    )

    assert portfolio.option_positions == {}

    # =====================================================
    # Position sizing
    #
    # $25,000 /
    # ($25 × 100)
    # = 10 contracts each
    #
    # Starting cash       100,000
    # Buy A               -25,000
    # Buy B               -25,000
    #                     -------
    # Cash after buys       50,000
    #
    # Sell A:
    # 10 × 30 × 100       +30,000
    #
    # Sell B:
    # 10 × 40 × 100       +40,000
    #
    # Final cash           120,000
    # =====================================================

    assert portfolio.cash == pytest.approx(
        120000.0
    )

    # A profit:
    # (30 - 25) × 10 × 100 = 5,000
    #
    # B profit:
    # (40 - 25) × 10 × 100 = 15,000
    #
    # Total = 20,000

    assert portfolio.realized_pnl == pytest.approx(
        20000.0
    )

def test_build_strategy_context_supports_daily_option_bar_provider():
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

            assert timestamp == pd.Timestamp(
                "2026-01-02"
            )
            assert contract == bar.contract

            return bar

    portfolio = Portfolio(
        initial_cash=100000,
    )

    portfolio.option_positions[contract] = OptionPosition(
        contract=contract,
        quantity=1,
        average_cost=25.0,
    )

    provider = FakeOptionBarProvider()

    engine = BacktestEngine()

    context = engine._build_strategy_context(
        timestamp=pd.Timestamp("2026-01-02"),
        portfolio=portfolio,
        option_data_provider=None,
        option_bar_provider=provider,
        option_pricing_policy=DailyCloseOptionPricingPolicy(),
    )

    assert len(provider.calls) == 1

    assert provider.calls[0] == (
        pd.Timestamp("2026-01-02"),
        contract,
    )

    assert contract in context.option_quotes

    quote = context.option_quotes[contract]

    assert quote.contract == contract
    assert quote.ask == 30.0
    assert quote.bid == 30.0
    assert quote.mark_price == 30.0

def test_backtest_engine_run_supports_daily_option_bar_provider():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    prices = pd.Series(
        [500.0],
        index=[
            pd.Timestamp("2026-01-02"),
        ],
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

    class BuyOptionStrategy:
        def on_bar(
            self,
            timestamp,
            price,
            context,
        ):
            return OptionOrder(
                contract=contract,
                action=Signal.BUY,
                quantity=1,
            )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    engine = BacktestEngine()

    engine.run(
        prices=prices,
        strategy=BuyOptionStrategy(),
        portfolio=portfolio,
        option_bar_provider=FakeOptionBarProvider(),
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    assert contract in portfolio.option_positions

    position = portfolio.option_positions[
        contract
    ]

    assert position.quantity == 1
    assert position.average_cost == 30.0

    assert portfolio.cash == 97000.0