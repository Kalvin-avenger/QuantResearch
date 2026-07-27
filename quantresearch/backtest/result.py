from dataclasses import dataclass

from quantresearch.portfolio import Portfolio


@dataclass
class BacktestResult:
    """
    Container for backtest output.
    """

    equity_curve: list[float]

    trades: list

    portfolio: Portfolio