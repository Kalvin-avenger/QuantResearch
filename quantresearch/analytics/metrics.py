from dataclasses import dataclass


@dataclass
class PerformanceMetrics:

    total_return: float

    cagr: float

    volatility: float

    sharpe: float

    max_drawdown: float


    def summary(self):

        return (
            "Performance Report\n"
            "==================\n"
            f"Total Return : {self.total_return:.2%}\n"
            f"CAGR         : {self.cagr:.2%}\n"
            f"Volatility   : {self.volatility:.2%}\n"
            f"Sharpe       : {self.sharpe:.2f}\n"
            f"Max Drawdown : {self.max_drawdown:.2%}"
        )