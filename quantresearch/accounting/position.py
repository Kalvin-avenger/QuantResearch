from dataclasses import dataclass


@dataclass(slots=True)
class Position:

    quantity: int = 0

    avg_price: float = 0.0


    def buy(
        self,
        quantity: int,
        price: float,
    ):

        if quantity <= 0:
            raise ValueError(
                "Quantity must be positive."
            )

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        total_cost = (
            self.quantity * self.avg_price
            +
            quantity * price
        )

        self.quantity += quantity

        self.avg_price = (
            total_cost
            /
            self.quantity
        )

    def sell(
        self,
        quantity: int,
        price: float,
    ) -> float:

        if quantity <= 0:
            raise ValueError(
                "Quantity must be positive."
            )

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        if quantity > self.quantity:
            raise ValueError(
                "Cannot sell more than current position."
            )

        realized_pnl = (
            price - self.avg_price
        ) * quantity

        self.quantity -= quantity

        if self.quantity == 0:
            self.avg_price = 0.0

        return realized_pnl