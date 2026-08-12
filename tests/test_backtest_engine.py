import pandas as pd

from quantresearch.backtest import (
    BacktestEngine,
    BacktestResult,
)
from quantresearch.portfolio import Portfolio
from quantresearch.strategy import MovingAverageStrategy
from quantresearch.signals import Signal
from quantresearch.strategy import BaseStrategy
from quantresearch.orders import Order
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

from quantresearch.data.options import OptionQuote
from quantresearch.orders.option_order import OptionOrder

from quantresearch.data.historical_options import (
    HistoricalOptionQuoteStore,
)


# def test_backtest_engine_basic():


#     prices = pd.Series(
#             [
#                 100,
#                 120,
#             ]
#         )

#     signals = [
#         Signal.BUY,
#         Signal.SELL,
#     ]


#     portfolio = Portfolio(
#         initial_cash=100000,
#     )

#     strategy = MovingAverageStrategy(
#         short_window=2,
#         long_window=3,
#     )

#     engine = BacktestEngine()

#     result = engine.run(
#         prices=prices,
#         strategy=strategy,
#         portfolio=portfolio,
#     )

#     assert result.equity_curve[-1] == 120000

def test_backtest_engine_allows_buy_when_position_already_exists():
    prices = pd.Series(
        [100.0],
        index=pd.to_datetime(["2026-01-02"]),
    )

    class BuyStrategy(BaseStrategy):
        def generate(self, prices):
            return [Signal.BUY]

    portfolio = Portfolio(
        initial_cash=1000,
    )

    portfolio.position.buy(
        quantity=2,
        price=100.0,
    )

    portfolio.cash = 800.0

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=BuyStrategy(),
        portfolio=portfolio,
    )

    assert result.portfolio.position.quantity == 10
    assert result.portfolio.cash == 0.0

    assert len(result.trades) == 1
    assert result.trades[0].action == Signal.BUY
    assert result.trades[0].quantity == 8
    assert result.trades[0].price == 100.0

def test_backtest_engine_respects_buy_fraction():
    prices = pd.Series(
        [100.0],
        index=pd.to_datetime(["2026-01-02"]),
    )

    class BuyStrategy(BaseStrategy):
        def generate(self, prices):
            return [Signal.BUY]

    portfolio = Portfolio(
        initial_cash=1000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=BuyStrategy(),
        portfolio=portfolio,
        buy_fraction=0.5,
    )

    assert result.portfolio.position.quantity == 5
    assert result.portfolio.cash == 500.0

    assert len(result.trades) == 1
    assert result.trades[0].quantity == 5

import pytest


@pytest.mark.parametrize(
    "buy_fraction",
    [0.0, -0.1, 1.1],
)
def test_backtest_engine_rejects_invalid_buy_fraction(
    buy_fraction,
):
    prices = pd.Series(
        [100.0],
        index=pd.to_datetime(["2026-01-02"]),
    )

    class BuyStrategy(BaseStrategy):
        def generate(self, prices):
            return [Signal.BUY]

    portfolio = Portfolio(
        initial_cash=1000,
    )

    engine = BacktestEngine()

    with pytest.raises(ValueError):
        engine.run(
            prices=prices,
            strategy=BuyStrategy(),
            portfolio=portfolio,
            buy_fraction=buy_fraction,
        )

def test_backtest_engine_supports_repeated_fractional_buys():
    prices = pd.Series(
        [100.0, 100.0],
        index=pd.to_datetime([
            "2026-01-02",
            "2026-01-05",
        ]),
    )

    class RepeatedBuyStrategy(BaseStrategy):
        def generate(self, prices):
            return [
                Signal.BUY,
                Signal.BUY,
            ]

    portfolio = Portfolio(
        initial_cash=1000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=RepeatedBuyStrategy(),
        portfolio=portfolio,
        buy_fraction=0.5,
    )

    assert result.portfolio.position.quantity == 7
    assert result.portfolio.cash == pytest.approx(300.0)

    assert len(result.trades) == 2

    assert result.trades[0].action == Signal.BUY
    assert result.trades[0].quantity == 5
    assert result.trades[0].price == 100.0

    assert result.trades[1].action == Signal.BUY
    assert result.trades[1].quantity == 2
    assert result.trades[1].price == 100.0

def test_backtest_engine_respects_sell_fraction():
    prices = pd.Series(
        [100.0],
        index=pd.to_datetime(["2026-01-02"]),
    )

    class SellStrategy(BaseStrategy):
        def generate(self, prices):
            return [Signal.SELL]

    portfolio = Portfolio(
        initial_cash=0,
    )

    portfolio.position.buy(
        quantity=10,
        price=80.0,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=SellStrategy(),
        portfolio=portfolio,
        sell_fraction=0.5,
    )

    assert result.portfolio.position.quantity == 5
    assert result.portfolio.cash == pytest.approx(500.0)

    assert len(result.trades) == 1
    assert result.trades[0].action == Signal.SELL
    assert result.trades[0].quantity == 5
    assert result.trades[0].price == 100.0

@pytest.mark.parametrize(
    "sell_fraction",
    [0.0, -0.1, 1.1],
)
def test_backtest_engine_rejects_invalid_sell_fraction(
    sell_fraction,
):
    prices = pd.Series(
        [100.0],
        index=pd.to_datetime(["2026-01-02"]),
    )

    class SellStrategy(BaseStrategy):
        def generate(self, prices):
            return [Signal.SELL]

    portfolio = Portfolio(
        initial_cash=0,
    )

    portfolio.position.buy(
        quantity=10,
        price=80.0,
    )

    engine = BacktestEngine()

    with pytest.raises(ValueError):
        engine.run(
            prices=prices,
            strategy=SellStrategy(),
            portfolio=portfolio,
            sell_fraction=sell_fraction,
        )

def test_backtest_engine_supports_repeated_partial_sells():
    prices = pd.Series(
        [100.0, 100.0],
        index=pd.to_datetime([
            "2026-01-02",
            "2026-01-05",
        ]),
    )

    class RepeatedSellStrategy(BaseStrategy):
        def generate(self, prices):
            return [
                Signal.SELL,
                Signal.SELL,
            ]

    portfolio = Portfolio(
        initial_cash=0,
    )

    portfolio.position.buy(
        quantity=10,
        price=80.0,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=RepeatedSellStrategy(),
        portfolio=portfolio,
        sell_fraction=0.5,
    )

    assert result.portfolio.position.quantity == 3
    assert result.portfolio.cash == pytest.approx(700.0)

    assert len(result.trades) == 2

    assert result.trades[0].action == Signal.SELL
    assert result.trades[0].quantity == 5
    assert result.trades[0].price == 100.0

    assert result.trades[1].action == Signal.SELL
    assert result.trades[1].quantity == 2
    assert result.trades[1].price == 100.0

def test_backtest_engine_executes_explicit_orders_from_strategy():
    prices = pd.Series(
        [100.0],
        index=pd.to_datetime(["2026-01-02"]),
    )

    class ExplicitOrderStrategy:
        def generate_orders(self, prices):
            return [
                Order(
                    action=Signal.BUY,
                    quantity=3,
                )
            ]

    portfolio = Portfolio(
        initial_cash=1000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=ExplicitOrderStrategy(),
        portfolio=portfolio,
    )

    assert result.portfolio.position.quantity == 3
    assert result.portfolio.cash == pytest.approx(700.0)

    assert len(result.trades) == 1
    assert result.trades[0].action == Signal.BUY
    assert result.trades[0].quantity == 3
    assert result.trades[0].price == 100.0

def test_backtest_engine_executes_explicit_sell_order_from_strategy():
    prices = pd.Series(
        [100.0],
        index=pd.to_datetime(["2026-01-02"]),
    )

    class ExplicitSellStrategy:
        def generate_orders(self, prices):
            return [
                Order(
                    action=Signal.SELL,
                    quantity=3,
                )
            ]

    portfolio = Portfolio(
        initial_cash=0,
    )

    portfolio.position.buy(
        quantity=10,
        price=80.0,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=ExplicitSellStrategy(),
        portfolio=portfolio,
    )

    assert result.portfolio.position.quantity == 7
    assert result.portfolio.cash == pytest.approx(300.0)

    assert len(result.trades) == 1
    assert result.trades[0].action == Signal.SELL
    assert result.trades[0].quantity == 3
    assert result.trades[0].price == 100.0

def test_backtest_engine_skips_none_explicit_orders():
    prices = pd.Series(
        [100.0, 110.0, 120.0],
        index=pd.to_datetime([
            "2026-01-02",
            "2026-01-05",
            "2026-01-06",
        ]),
    )

    class SparseOrderStrategy:
        def generate_orders(self, prices):
            return [
                None,
                Order(
                    action=Signal.BUY,
                    quantity=2,
                ),
                None,
            ]

    portfolio = Portfolio(
        initial_cash=1000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=SparseOrderStrategy(),
        portfolio=portfolio,
    )

    assert result.portfolio.position.quantity == 2
    assert result.portfolio.cash == pytest.approx(780.0)

    assert len(result.trades) == 1
    assert result.trades[0].action == Signal.BUY
    assert result.trades[0].quantity == 2
    assert result.trades[0].price == 110.0

    assert len(result.equity_curve) == 3

def test_backtest_engine_rejects_mismatched_explicit_order_length():
    prices = pd.Series(
        [100.0, 110.0, 120.0],
        index=pd.to_datetime([
            "2026-01-02",
            "2026-01-05",
            "2026-01-06",
        ]),
    )

    class InvalidOrderStrategy:
        def generate_orders(self, prices):
            return [
                None,
                Order(
                    action=Signal.BUY,
                    quantity=2,
                ),
            ]

    portfolio = Portfolio(
        initial_cash=1000,
    )

    engine = BacktestEngine()

    with pytest.raises(ValueError):
        engine.run(
            prices=prices,
            strategy=InvalidOrderStrategy(),
            portfolio=portfolio,
        )

# def test_backtest_engine_accepts_option_quotes_by_timestamp():
#     timestamp = pd.Timestamp("2026-01-02")

#     prices = pd.Series(
#         [500.0],
#         index=[timestamp],
#     )

#     contract = OptionContract(
#         underlying="SPY",
#         expiration=pd.Timestamp("2027-12-17"),
#         strike=500.0,
#         option_type=OptionType.CALL,
#     )

#     quote = OptionQuote(
#         contract=contract,
#         last_trade_date=timestamp,
#         last_price=25.0,
#         bid=24.5,
#         ask=25.5,
#         volume=100,
#         open_interest=1000,
#         implied_volatility=0.20,
#         in_the_money=False,
#     )

#     option_quotes = {
#         timestamp: {
#             contract: quote,
#         }
#     }

#     class NoTradeStrategy(BaseStrategy):
#         def generate(self, prices):
#             return [Signal.HOLD]

#     portfolio = Portfolio(
#         initial_cash=100000,
#     )

#     engine = BacktestEngine()

#     result = engine.run(
#         prices=prices,
#         strategy=NoTradeStrategy(),
#         portfolio=portfolio,
#         option_quotes=option_quotes,
#     )

#     assert len(result.equity_curve) == 1
#     assert result.portfolio.cash == 100000

def test_backtest_engine_executes_explicit_option_buy_order():
    timestamp = pd.Timestamp("2026-01-02")

    prices = pd.Series(
        [500.0],
        index=[timestamp],
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=contract,
        last_trade_date=timestamp,
        last_price=25.0,
        bid=24.5,
        ask=25.5,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    class OptionBuyStrategy:
        def generate_orders(self, prices):
            return [
                OptionOrder(
                    contract=contract,
                    action=Signal.BUY,
                    quantity=2,
                )
            ]

    provider = HistoricalOptionQuoteStore(
    quotes={
        timestamp: {
            contract: quote,
        }
    }
)

    portfolio = Portfolio(
        initial_cash=100000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=OptionBuyStrategy(),
        portfolio=portfolio,
        option_data_provider=provider,
    )

    position = result.portfolio.option_positions[contract]

    assert position.quantity == 2
    assert position.average_cost == pytest.approx(25.5)

    assert result.portfolio.cash == pytest.approx(94900.0)

def test_backtest_engine_uses_option_data_provider_for_option_order():
    timestamp = pd.Timestamp("2026-01-02")

    prices = pd.Series(
        [500.0],
        index=[timestamp],
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=contract,
        last_trade_date=timestamp,
        last_price=25.0,
        bid=24.5,
        ask=25.5,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    provider = HistoricalOptionQuoteStore(
        quotes={
            timestamp: {
                contract: quote,
            }
        }
    )

    class OptionBuyStrategy:
        def generate_orders(self, prices):
            return [
                OptionOrder(
                    contract=contract,
                    action=Signal.BUY,
                    quantity=2,
                )
            ]

    portfolio = Portfolio(
        initial_cash=100000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=OptionBuyStrategy(),
        portfolio=portfolio,
        option_data_provider=provider,
    )

    position = result.portfolio.option_positions[contract]

    assert position.quantity == 2
    assert position.average_cost == pytest.approx(25.5)
    assert result.portfolio.cash == pytest.approx(94900.0)

def test_backtest_engine_preserves_portfolio_when_option_quote_is_missing():
    timestamp = pd.Timestamp("2026-01-02")

    prices = pd.Series(
        [500.0],
        index=[timestamp],
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    provider = HistoricalOptionQuoteStore(
        quotes={}
    )

    class OptionBuyStrategy:
        def generate_orders(self, prices):
            return [
                OptionOrder(
                    contract=contract,
                    action=Signal.BUY,
                    quantity=2,
                )
            ]

    portfolio = Portfolio(
        initial_cash=100000,
    )

    engine = BacktestEngine()

    with pytest.raises(
        ValueError,
        match="timestamp",
    ):
        engine.run(
            prices=prices,
            strategy=OptionBuyStrategy(),
            portfolio=portfolio,
            option_data_provider=provider,
        )

    assert portfolio.cash == 100000
    assert contract not in portfolio.option_positions

def test_backtest_engine_accepts_option_data_provider():
    timestamp = pd.Timestamp("2026-01-02")

    prices = pd.Series(
        [500.0],
        index=[timestamp],
    )

    provider = HistoricalOptionQuoteStore(
        quotes={}
    )

    class NoTradeStrategy(BaseStrategy):
        def generate(self, prices):
            return [Signal.HOLD]

    portfolio = Portfolio(
        initial_cash=100000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=NoTradeStrategy(),
        portfolio=portfolio,
        option_data_provider=provider,
    )

    assert len(result.equity_curve) == 1
    assert result.portfolio.cash == 100000

