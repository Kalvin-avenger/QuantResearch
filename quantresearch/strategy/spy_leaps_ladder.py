from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)
from quantresearch.orders.option_order import (
    OptionOrder,
)
from quantresearch.signals import Signal

from quantresearch.strategy.spy_leaps_tranche import (
    SpyLeapsTranche,
)
from quantresearch.strategy.leaps_contract_resolver import (
    FixedLeapsContractResolver,
)


class SpyLeapsLadderStrategy:

    def __init__(
        self,
        leaps_contract=None,
        contract_resolver=None,
        equity_allocation: float = 0.25,
        option_allocation: float = 0.25,
        drawdown_step: float = 0.05,
        initial_capital: float | None = None,
        max_tranches: int = 2,
        take_profit_threshold: float = 0.25,
    ):

        # =====================================================
        # Contract configuration
        # =====================================================

        if contract_resolver is None:

            if leaps_contract is None:
                raise ValueError(
                    "Either leaps_contract or contract_resolver "
                    "must be provided"
                )

            contract_resolver = FixedLeapsContractResolver(
                contract=leaps_contract,
            )

        if (
            leaps_contract is None
            and isinstance(
                contract_resolver,
                FixedLeapsContractResolver,
            )
        ):
            leaps_contract = contract_resolver.contract

        self.leaps_contract = leaps_contract
        self.contract_resolver = contract_resolver

        # =====================================================
        # Strategy configuration
        # =====================================================

        self.equity_allocation = equity_allocation
        self.option_allocation = option_allocation
        self.drawdown_step = drawdown_step
        self.initial_capital = initial_capital

        self.max_tranches = max_tranches

        self.take_profit_threshold = (
            take_profit_threshold
        )

        # =====================================================
        # Runtime state
        # =====================================================

        self.peak_price = None
        self.last_triggered_level = 0

        self.tranches = []

    # =========================================================
    # Legacy instruction generation
    # =========================================================

    def generate_equity_instruction(
        self,
    ):

        return EquityOrderIntent(
            action=Signal.BUY,
            allocation_fraction=self.equity_allocation,
            allocation_base=self.initial_capital,
        )

    def generate_option_instruction(
        self,
    ):

        return self.generate_option_instruction_for_contract(
            contract=self.leaps_contract,
        )

    def generate_initial_instructions(
        self,
    ):

        return [
            self.generate_equity_instruction(),
            self.generate_option_instruction(),
        ]

    def find_take_profit_orders(
        self,
        context,
    ):

        orders = []

        for contract in (
            self.get_active_option_contracts()
        ):

            position = (
                context.option_positions.get(
                    contract
                )
            )

            quote = (
                context.option_quotes.get(
                    contract
                )
            )

            if position is None:
                continue

            if position.quantity <= 0:
                continue

            if quote is None:
                continue

            if not self.should_take_profit(
                current_bid=quote.bid,
                average_cost=position.average_cost,
            ):
                continue

            orders.append(
                OptionOrder(
                    contract=contract,
                    action=Signal.SELL,
                    quantity=position.quantity,
                )
            )

        return orders

    # =========================================================
    # Runtime contract resolution
    # =========================================================

    def resolve_leaps_contract(
        self,
        timestamp,
        underlying_price: float,
    ):

        return self.contract_resolver.resolve(
            timestamp=timestamp,
            underlying_price=underlying_price,
        )

    def generate_runtime_option_instruction(
        self,
        timestamp,
        underlying_price: float,
    ):

        contract = self.resolve_leaps_contract(
            timestamp=timestamp,
            underlying_price=underlying_price,
        )

        return self.generate_option_instruction_for_contract(
            contract=contract,
        )

    def generate_option_instruction_for_contract(
        self,
        contract,
    ):

        return OptionOrderIntent(
            contract=contract,
            action=Signal.BUY,
            allocation_fraction=self.option_allocation,
            allocation_base=self.initial_capital,
        )

    # =========================================================
    # Tranche state
    # =========================================================

    def create_tranche(
        self,
        level: int,
        deploy_equity: bool,
        deploy_option: bool,
        option_contract=None,
    ) -> SpyLeapsTranche:

        tranche = SpyLeapsTranche(
            level=level,
        )

        if deploy_equity:
            tranche.deploy_equity()

        if deploy_option:
            tranche.deploy_option(
                contract=option_contract,
            )
        self.tranches.append(
            tranche
        )

        return tranche

    def create_deployed_tranche(
        self,
        level: int,
        option_contract=None,
    ) -> SpyLeapsTranche:

        return self.create_tranche(
            level=level,
            deploy_equity=True,
            deploy_option=True,
            option_contract=option_contract,
        )

    def close_deployed_option_legs(
        self,
    ) -> None:

        for tranche in self.tranches:

            if tranche.option_deployed:
                tranche.close_option()

    @property
    def active_equity_tranches(
        self,
    ) -> int:

        return sum(
            1
            for tranche in self.tranches
            if tranche.equity_deployed
        )

    @property
    def active_option_tranches(
        self,
    ) -> int:

        return sum(
            1
            for tranche in self.tranches
            if tranche.option_deployed
        )

    # =========================================================
    # Legacy vectorized path
    # =========================================================

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
        self.tranches = []

        for index, price in enumerate(prices):

            price = float(price)

            # -------------------------------------------------
            # Initial tranche
            # -------------------------------------------------

            if index == 0:

                self.peak_price = price

                orders[index] = (
                    self.generate_initial_instructions()
                )

                self.create_deployed_tranche(
                    level=0,
                )

                continue

            # -------------------------------------------------
            # Drawdown tranche
            # -------------------------------------------------

            triggered_level = (
                self.update_drawdown_state(
                    price=price,
                )
            )

            if (
                triggered_level is not None
                and self.active_equity_tranches
                < self.max_tranches
            ):

                orders[index] = (
                    self.generate_initial_instructions()
                )

                self.create_deployed_tranche(
                    level=triggered_level,
                )

        return orders

    # =========================================================
    # Drawdown logic
    # =========================================================

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

    def update_peak(
        self,
        price: float,
    ) -> bool:

        if self.peak_price is None:

            self.peak_price = price

            return True

        if price > self.peak_price:

            self.peak_price = price
            self.last_triggered_level = 0

            return True

        return False

    def update_drawdown_state(
        self,
        price: float,
    ) -> int | None:

        if self.peak_price is None:

            self.update_peak(
                price=price,
            )

            return None

        if price > self.peak_price:

            self.update_peak(
                price=price,
            )

            return None

        level = self.drawdown_level(
            price=price,
            peak_price=self.peak_price,
        )

        if level <= self.last_triggered_level:
            return None

        self.last_triggered_level = level

        return level

    # =========================================================
    # Option take-profit
    # =========================================================

    def calculate_option_return(
        self,
        current_bid: float,
        average_cost: float,
    ) -> float:

        if average_cost <= 0:
            raise ValueError(
                "average_cost must be positive"
            )

        return (
            current_bid / average_cost
        ) - 1.0

    def should_take_profit(
        self,
        current_bid: float,
        average_cost: float,
    ) -> bool:

        option_return = (
            self.calculate_option_return(
                current_bid=current_bid,
                average_cost=average_cost,
            )
        )

        return (
            option_return
            >= self.take_profit_threshold
        )

    def get_active_option_contracts(
        self,
    ):

        contracts = []

        for tranche in self.tranches:

            if not tranche.option_deployed:
                continue

            if tranche.option_contract is None:
                continue

            contracts.append(
                tranche.option_contract
            )

        return contracts

    def close_option_contract(
        self,
        contract,
    ) -> None:

        for tranche in self.tranches:

            if (
                tranche.option_deployed
                and tranche.option_contract == contract
            ):
                tranche.close_option()

    def find_take_profit_order(
        self,
        context,
    ):

        for contract in (
            self.get_active_option_contracts()
        ):

            position = (
                context.option_positions.get(
                    contract
                )
            )

            quote = (
                context.option_quotes.get(
                    contract
                )
            )

            if position is None:
                continue

            if position.quantity <= 0:
                continue

            if quote is None:
                continue

            if not self.should_take_profit(
                current_bid=quote.bid,
                average_cost=position.average_cost,
            ):
                continue

            return OptionOrder(
                contract=contract,
                action=Signal.SELL,
                quantity=position.quantity,
            )

        return None

    # =========================================================
    # Runtime strategy path
    # =========================================================

    def on_bar(
        self,
        timestamp,
        price: float,
        context,
    ):

        price = float(price)

        # =========================================
        # First bar
        # =========================================

        # if self.peak_price is None:

        #     self.peak_price = price
        #     self.last_triggered_level = 0

        #     if self.initial_capital is None:
        #         self.initial_capital = context.cash

        #     contract = self.resolve_leaps_contract(
        #         timestamp=timestamp,
        #         underlying_price=price,
        #     )

        #     self.create_deployed_tranche(
        #         level=0,
        #         option_contract=contract,
        #     )

        #     return [
        #         self.generate_equity_instruction(),
        #         self.generate_option_instruction_for_contract(
        #             contract=contract,
        #         ),
        #     ]

        take_profit_orders = (
            self.find_take_profit_orders(
                context=context,
            )
        )

        if take_profit_orders:

            order = take_profit_orders[0]

            self.close_option_contract(
                order.contract
            )

            return order

        # =========================================
        # Update peak before any early return
        # =========================================

        if price > self.peak_price:

            self.update_peak(
                price=price,
            )

        # =========================================
        # LEAPS take-profit
        #
        # IMPORTANT:
        # This still uses the legacy fixed contract.
        # Dynamic multi-contract take-profit will be
        # handled in a later Sprint.
        # =========================================

        # if self.leaps_contract is not None:

        #     position = context.option_positions.get(
        #         self.leaps_contract
        #     )

        #     quote = context.option_quotes.get(
        #         self.leaps_contract
        #     )

        #     if (
        #         position is not None
        #         and position.quantity > 0
        #         and quote is not None
        #         and self.should_take_profit(
        #             current_bid=quote.bid,
        #             average_cost=position.average_cost,
        #         )
        #     ):

        #         self.close_deployed_option_legs()

        #         return OptionOrder(
        #             contract=self.leaps_contract,
        #             action=Signal.SELL,
        #             quantity=position.quantity,
        #         )

        take_profit_order = (
            self.find_take_profit_order(
                context=context,
            )
        )

        if take_profit_order is not None:

            self.close_option_contract(
                take_profit_order.contract
            )

            return take_profit_order

        # =========================================
        # Drawdown ladder
        # =========================================

        triggered_level = (
            self.update_drawdown_state(
                price=price,
            )
        )

        if triggered_level is None:
            return None

        # =========================================
        # Independent capacity
        # =========================================

        can_deploy_equity = (
            self.active_equity_tranches
            < self.max_tranches
        )

        can_deploy_option = (
            self.active_option_tranches
            < self.max_tranches
        )

        if (
            not can_deploy_equity
            and not can_deploy_option
        ):
            return None

        instructions = []

        resolved_option_contract = None

        # =========================================
        # Equity leg
        # =========================================

        if can_deploy_equity:

            instructions.append(
                self.generate_equity_instruction()
            )

        # =========================================
        # Option leg
        # =========================================

        if can_deploy_option:

            resolved_option_contract = (
                self.resolve_leaps_contract(
                    timestamp=timestamp,
                    underlying_price=price,
                )
            )

            instructions.append(
                self.generate_option_instruction_for_contract(
                    contract=resolved_option_contract,
                )
            )

        # =========================================
        # Record lifecycle state
        # =========================================

        self.create_tranche(
            level=triggered_level,
            deploy_equity=can_deploy_equity,
            deploy_option=can_deploy_option,
            option_contract=resolved_option_contract,
        )

        return instructions