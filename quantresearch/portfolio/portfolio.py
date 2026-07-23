class Portfolio:
    """
    Simple long-only portfolio.

    Uses all available cash when buying.
    """

    def __init__(
        self,
        initial_cash: float,
    ):

        self.cash = initial_cash
        self.shares = 0


    def buy(
        self,
        price: float,
    ):

        if self.cash <= 0:
            return


        self.shares = int(
            self.cash // price
        )


        self.cash -= (
            self.shares * price
        )


    def sell(
        self,
        price: float,
    ):

        if self.shares <= 0:
            return


        self.cash += (
            self.shares * price
        )


        self.shares = 0