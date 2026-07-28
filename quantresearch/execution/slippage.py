class FixedSlippageModel:
    def __init__(self, slippage: float = 0.0):
        if slippage < 0:
            raise ValueError("Slippage must be non-negative.")

        self.slippage = slippage

    def apply(self, price: float, side: str) -> float:
        side = side.upper()

        if side == "BUY":
            return price * (1 + self.slippage)

        if side == "SELL":
            return price * (1 - self.slippage)

        raise ValueError(f"Unsupported side: {side}")