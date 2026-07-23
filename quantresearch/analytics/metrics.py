from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """
    Performance statistics of a strategy.
    """

    total_return: float

    cagr: float

    volatility: float

    sharpe: float

    max_drawdown: float