from quantresearch.indicators.moving_average import calculate_sma
from quantresearch.signals.crossover import generate_crossover_signal

from .base import BaseStrategy
import pandas as pd


class MovingAverageStrategy(BaseStrategy):

    """
    Generate trading signals.

    Args:
        prices:
            Price series.

    Returns:
        Trading signal series.
    """

    def __init__(
        self,
        short_window: int,
        long_window: int,
    ):

        self.short_window = short_window
        self.long_window = long_window

        if short_window >= long_window:
            raise ValueError(
                "short_window must be smaller than long_window."
            )

    def generate(
        self,
        prices: pd.Series,
    ) -> pd.Series:

        short_ma = calculate_sma(
            prices,
            self.short_window,
        )

        long_ma = calculate_sma(
            prices,
            self.long_window,
        )

        return generate_crossover_signal(
            short_ma,
            long_ma,
        )