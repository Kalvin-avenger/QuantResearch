import numpy as np

from .metrics import PerformanceMetrics



class PerformanceAnalyzer:


    def calculate(
        self,
        equity_curve,
    ):

        total_return = (
            equity_curve[-1]
            /
            equity_curve[0]
            -
            1
        )


        return PerformanceMetrics(
            total_return=total_return,
            cagr=0,
            volatility=0,
            sharpe=0,
            max_drawdown=0,
        )