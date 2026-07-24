class BaseStrategy:

    """
    Base class for all trading strategies.
    """

    def generate(self, prices):
        raise NotImplementedError(
            "Strategy must implement generate()."
        )