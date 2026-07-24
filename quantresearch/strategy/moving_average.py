from quantresearch.indicators.moving_average import calculate_sma
from quantresearch.signals.crossover import generate_crossover_signal

from .base import BaseStrategy


class MovingAverageStrategy(BaseStrategy):

    def __init__(
        self,
        short_window,
        long_window,
    ):

        self.short_window = short_window
        self.long_window = long_window

    def generate(self, prices):

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