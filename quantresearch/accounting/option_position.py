from dataclasses import dataclass

from quantresearch.instruments.options import (
    OptionContract,
)


@dataclass
class OptionPosition:
    contract: OptionContract
    quantity: int
    average_cost: float

    def __post_init__(self):

        if self.quantity < 0:
            raise ValueError(
                "quantity must not be negative"
            )

        if self.average_cost < 0:
            raise ValueError(
                "average_cost must not be negative"
            )

        if (
            self.quantity == 0
            and self.average_cost != 0
        ):
            raise ValueError(
                "average_cost must be zero "
                "when quantity is zero"
            )

    def market_value(
        self,
        current_price: float,
    ) -> float:

        self._validate_market_price(
            current_price
        )

        return (
            self.quantity
            * self.contract.multiplier
            * current_price
        )

    def unrealized_pnl(
        self,
        current_price: float,
    ) -> float:

        self._validate_market_price(
            current_price
        )

        return (
            current_price
            - self.average_cost
        ) * self.quantity * self.contract.multiplier

    def return_pct(
        self,
        current_price: float,
    ) -> float:

        self._validate_market_price(
            current_price
        )

        if self.average_cost == 0:
            return 0.0

        return (
            current_price
            / self.average_cost
            - 1
        )

    def buy(
        self,
        quantity: int,
        price: float,
    ) -> None:

        self._validate_trade_input(
            quantity=quantity,
            price=price,
        )

        total_cost = (
            self.quantity
            * self.average_cost
            + quantity
            * price
        )

        self.quantity += quantity

        self.average_cost = (
            total_cost
            / self.quantity
        )

    def sell(
        self,
        quantity: int,
        price: float,
    ) -> float:

        self._validate_trade_input(
            quantity=quantity,
            price=price,
        )

        if quantity > self.quantity:
            raise ValueError(
                "quantity exceeds current position"
            )

        realized_pnl = (
            price
            - self.average_cost
        ) * quantity * self.contract.multiplier

        self.quantity -= quantity

        if self.quantity == 0:
            self.average_cost = 0.0

        return realized_pnl

    @staticmethod
    def _validate_trade_input(
        quantity: int,
        price: float,
    ) -> None:

        if quantity <= 0:
            raise ValueError(
                "quantity must be positive"
            )

        if price <= 0:
            raise ValueError(
                "price must be positive"
            )

    @staticmethod
    def _validate_market_price(
        current_price: float,
    ) -> None:

        if current_price < 0:
            raise ValueError(
                "current_price must not be negative"
            )