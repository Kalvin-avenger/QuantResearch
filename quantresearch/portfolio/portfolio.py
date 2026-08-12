from quantresearch.signals import Signal
from quantresearch.accounting import Position
from quantresearch.accounting.option_position import OptionPosition
from quantresearch.execution.option_execution import OptionExecutionResult
from quantresearch.instruments.options import OptionContract


class Portfolio:
    """
    Simple long-only portfolio.

    Uses all available cash when buying.
    """

    def __init__(
        self,
        initial_cash: float,
        
    ):

        if initial_cash < 0:
            raise ValueError(
                "Initial cash cannot be negative."
            )

        self.cash = initial_cash
        self.position = Position()
        self.realized_pnl = 0.0
        self.option_positions = {}

    def buy(
        self,
        price: float,
    ) -> None:

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        if self.cash <= 0:
            return

        quantity = int(
            self.cash // price
        )

        if quantity <= 0:
            return

        cost = quantity * price

        self.cash -= cost

        self.position.buy(
            quantity=quantity,
            price=price,
        )

    def sell(
        self,
        price: float,
    ) -> None:

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        quantity = self.position.quantity

        if quantity <= 0:
            return

        self.position.sell(
            quantity=quantity,
            price=price,
        )

        self.cash += quantity * price

    def apply_execution(
        self,
        execution,
    ) -> None:

        quantity = execution.order.quantity
        price = execution.execution_price
        action = execution.order.action

        if action == Signal.BUY:

            cost = quantity * price

            if cost > self.cash:
                raise ValueError(
                    "Insufficient cash."
                )

            self.cash -= cost

            self.position.buy(
                quantity=quantity,
                price=price,
            )

        elif action == Signal.SELL:

            realized_pnl = self.position.sell(
                quantity=quantity,
                price=price,
            )

            self.cash += quantity * price

            self.realized_pnl += realized_pnl

    def market_value(
        self,
        price: float,
    ) -> float:

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        return (
            self.position.quantity
            * price
        )

    def unrealized_pnl(
        self,
        price: float,
    ) -> float:

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        return (
            price - self.position.avg_price
        ) * self.position.quantity

    def total_equity(
        self,
        price: float,
        option_prices: dict[OptionContract, float] | None = None,
    ) -> float:
        equity_value = self.market_value(price)

        option_value = 0.0

        if option_prices is not None:
            option_value = self.option_market_value(option_prices)

        return self.cash + equity_value + option_value

    def add_option_position(
        self,
        position: OptionPosition,
    ) -> None:
        if position.contract in self.option_positions:
            raise ValueError("option position already exists")

        self.option_positions[position.contract] = position


    def apply_option_execution(
        self,
        execution: OptionExecutionResult,
    ) -> None:
        order = execution.order
        contract = order.contract

        if order.action == Signal.BUY:
            cost = (
                order.quantity
                * execution.execution_price
                * contract.multiplier
            )

            if cost > self.cash:
                raise ValueError("insufficient cash for option purchase")

            self.cash -= cost

            if contract in self.option_positions:
                self.option_positions[contract].buy(
                    quantity=order.quantity,
                    price=execution.execution_price,
                )
            else:
                position = OptionPosition(
                    contract=contract,
                    quantity=order.quantity,
                    average_cost=execution.execution_price,
                )

                self.add_option_position(position)

        else:
            if contract not in self.option_positions:
                raise ValueError("option position does not exist")

            position = self.option_positions[contract]

            position.sell(
                quantity=order.quantity,
                price=execution.execution_price,
            )

            proceeds = (
                order.quantity
                * execution.execution_price
                * contract.multiplier
            )

            self.cash += proceeds

            if position.quantity == 0:
                del self.option_positions[contract]

    def option_market_value(
        self,
        option_prices: dict,
    ) -> float:
        total = 0.0

        for contract, position in self.option_positions.items():
            current_price = option_prices[contract]
            total += position.market_value(current_price)

        return total

