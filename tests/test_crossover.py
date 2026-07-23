import pandas as pd

from quantresearch.signals import Signal
from quantresearch.signals.crossover import (
    generate_crossover_signal,
)

def test_generate_crossover_signal():
    short_ma = pd.Series(
    [1, 2, 3, 4, 5, 4, 3]
    )

    long_ma = pd.Series(
        [3, 3, 3, 3, 3, 3, 3]
    )

expected = [
    Signal.NONE,
    Signal.NONE,
    Signal.HOLD,
    Signal.BUY,
    Signal.HOLD,
    Signal.HOLD,
    Signal.SELL,
]