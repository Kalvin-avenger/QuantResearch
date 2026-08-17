from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)
from quantresearch.signals import Signal


class SpyLeapsLadderStrategy:

    def __init__(
        self,
        leaps_contract,
        equity_allocation: float = 0.25,
        option_allocation: float = 0.25,
        drawdown_step: float = 0.05,
        initial_capital: float | None = None,

        max_tranches: int = 2,
    ):
        self.leaps_contract = leaps_contract
        self.equity_allocation = equity_allocation
        self.option_allocation = option_allocation
        self.drawdown_step = drawdown_step
        self.initial_capital = initial_capital

        self.peak_price = None
        self.last_triggered_level = 0

        self.max_tranches = max_tranches
        self.tranches_deployed = 0

    def generate_initial_instructions(self):

        equity_instruction = EquityOrderIntent(
            action=Signal.BUY,
            allocation_fraction=self.equity_allocation,
            allocation_base=self.initial_capital,
        )

        option_instruction = OptionOrderIntent(
            contract=self.leaps_contract,
            action=Signal.BUY,
            allocation_fraction=self.option_allocation,
            allocation_base=self.initial_capital,
        )

        return [
            equity_instruction,
            option_instruction,
        ]

    def generate_orders(
        self,
        prices,
    ):

        if len(prices) == 0:
            return []

        orders = [
            None
            for _ in range(len(prices))
        ]

        self.peak_price = None
        self.last_triggered_level = 0
        self.tranches_deployed = 0

        for index, price in enumerate(prices):

            if index == 0:

                self.peak_price = float(price)

                orders[index] = (
                    self.generate_initial_instructions()
                )

                self.tranches_deployed = 1

                continue

            triggered_level = (
                self.update_drawdown_state(
                    price=float(price),
                )
            )

            if (
                triggered_level is not None
                and self.tranches_deployed
                < self.max_tranches
            ):

                orders[index] = (
                    self.generate_initial_instructions()
                )

                self.tranches_deployed += 1

        return orders

    def calculate_drawdown(
        self,
        price: float,
        peak_price: float,
    ) -> float:

        if peak_price <= 0:
            raise ValueError(
                "peak_price must be positive"
            )

        return (
            price / peak_price
        ) - 1.0

    def drawdown_level(
        self,
        price: float,
        peak_price: float,
    ) -> int:

        drawdown = self.calculate_drawdown(
            price=price,
            peak_price=peak_price,
        )

        if drawdown >= 0:
            return 0

        tolerance = 1e-12

        return int(
            (
                abs(drawdown)
                + tolerance
            )
            / self.drawdown_step
        )

    def update_drawdown_state(
        self,
        price: float,
    ) -> int | None:

        if self.peak_price is None:
            self.peak_price = price
            return None

        if price > self.peak_price:
            self.peak_price = price
            self.last_triggered_level = 0
            return None

        level = self.drawdown_level(
            price=price,
            peak_price=self.peak_price,
        )

        if level <= self.last_triggered_level:
            return None

        self.last_triggered_level = level

        return level