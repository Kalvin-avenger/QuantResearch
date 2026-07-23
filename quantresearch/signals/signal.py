from enum import Enum


class Signal(Enum):
    """
    Trading signal types.
    """

    NONE = 0
    HOLD = 1
    BUY = 2
    SELL = 3