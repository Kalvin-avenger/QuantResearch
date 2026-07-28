from quantresearch.analytics.analyzer import PerformanceAnalyzer
from quantresearch.backtest.engine import BacktestEngine
from quantresearch.data.yahoo import download_price_data
from quantresearch.portfolio import Portfolio
from quantresearch.strategy import MovingAverageStrategy


def test_ma_strategy_end_to_end():

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

    report = PerformanceAnalyzer().calculate(
        result.equity_curve
    )

    assert len(result.equity_curve) == len(prices)

    assert report.total_return > -1