import numpy as np

from .metrics import PerformanceMetrics


class PerformanceAnalyzer:


    def calculate(
        self,
        equity_curve,
    ):

        equity = np.array(
            equity_curve,
            dtype=float
        )


        total_return = (
            equity[-1]
            /
            equity[0]
            -
            1
        )


        periods = len(equity)-1


        cagr = (
            equity[-1]
            /
            equity[0]
        ) ** (
            252 / periods
        ) - 1


        daily_returns = (
            equity[1:]
            /
            equity[:-1]
            -
            1
        )


        volatility = (
            np.std(
                daily_returns,
                ddof=1
            )
            *
            np.sqrt(252)
        )


        daily_std = np.std(
            daily_returns,
            ddof=1
        )


        if daily_std != 0:

            sharpe = (
                np.mean(daily_returns)
                /
                daily_std
                *
                np.sqrt(252)
            )

        else:

            sharpe = 0


        running_max = np.maximum.accumulate(
            equity
        )

        drawdown = (
            equity-running_max
        ) / running_max


        max_drawdown = drawdown.min()


        return PerformanceMetrics(
            total_return,
            cagr,
            volatility,
            sharpe,
            max_drawdown,
        )