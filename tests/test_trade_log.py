from quantresearch.backtest.engine import BacktestEngine
from quantresearch.portfolio import Portfolio
from quantresearch.strategy import MovingAverageStrategy
from quantresearch.data.yahoo import download_price_data
import pandas as pd


def test_backtest_generates_trade_log():

    prices = download_price_data(
        ticker="AAPL",
        start_date="2023-01-01",
        end_date="2024-01-01",
    )

    strategy = MovingAverageStrategy(
        short_window=20,
        long_window=50,
    )

    portfolio = Portfolio(
        initial_cash=10000,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices["close"],
        strategy,
        portfolio,
    )

    assert isinstance(result.trades, list)

    assert len(result.trades) > 0

def test_trade_contains_timestamp():

    prices = download_price_data(
        ticker="AAPL",
        start_date="2023-01-01",
        end_date="2024-01-01",
    )

    strategy = MovingAverageStrategy(
        short_window=20,
        long_window=50,
    )

    portfolio = Portfolio(
        initial_cash=10000,
    )

    engine = BacktestEngine()

    prices_series = (
    prices
    .set_index("date")["close"]
)


    result = engine.run(
        prices_series,
        strategy,
        portfolio,
    )

    assert len(result.trades) > 0

    assert isinstance(
        result.trades[0].timestamp,
        pd.Timestamp,
    )