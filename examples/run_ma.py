from quantresearch.analytics.analyzer import PerformanceAnalyzer
from quantresearch.backtest.engine import BacktestEngine
from quantresearch.data.yahoo import download_price_data
from quantresearch.portfolio import Portfolio
from quantresearch.strategy import MovingAverageStrategy



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

print("========== Performance ==========")
print(f"Total Return : {report.total_return:.2%}")
print(f"CAGR         : {report.cagr:.2%}")
print(f"Volatility   : {report.volatility:.2%}")
print(f"Sharpe Ratio : {report.sharpe:.2f}")
print(f"Max Drawdown : {report.max_drawdown:.2%}")