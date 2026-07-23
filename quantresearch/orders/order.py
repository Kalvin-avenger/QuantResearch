from dataclasses import dataclass
from typing import Optional

from quantresearch.signals import Signal


@dataclass
class Order:
    """
    Trading order.

    Parameters
    ----------
    action:
        Trading signal action.

    quantity:
        Number of shares.

    price:
        Execution price.
    """

    action: Signal
    quantity: int
    price: Optional[float] = None