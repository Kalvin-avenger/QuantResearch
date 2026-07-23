from dataclasses import dataclass
from typing import Any


@dataclass
class BacktestResult:
    """
    Container for backtest output.
    """

    equity_curve: Any

    trades: list