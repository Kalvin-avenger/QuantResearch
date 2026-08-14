import pandas as pd

from quantresearch.strategy import BaseStrategy
from quantresearch.execution import Executor, Trade
from quantresearch.orders import Order
from quantresearch.portfolio import Portfolio
from quantresearch.signals import Signal
from quantresearch.backtest import BacktestResult
from quantresearch.orders.option_order import OptionOrder
from quantresearch.execution.option_execution import OptionExecutor
from quantresearch.data.options import OptionQuote
from quantresearch.data.option_provider import (
    HistoricalOptionDataProvider,
)
from quantresearch.execution.option_quote_protocol import (
    ExecutableOptionQuote,
)
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)

# from quantresearch.orders.option_order_builder import (
#     OptionOrderBuilder,
# )

from quantresearch.orders.option_instruction_resolver import (
    OptionInstructionResolver,
)

from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)

from quantresearch.orders.equity_instruction_resolver import (
    EquityInstructionResolver,
)

class BacktestEngine:
    """
    Simple backtest engine.

    Assumptions
    -----------
    - Single asset
    - Long only
    - Market execution
    - No commission
    - No slippage
    """

    def __init__(self):

        self.executor = Executor()
        self.option_executor = OptionExecutor()
        self.option_instruction_resolver = (
            OptionInstructionResolver()
        )
        self.equity_instruction_resolver = (
            EquityInstructionResolver()
        )

    def _calculate_buy_quantity(
        self,
        portfolio: Portfolio,
        price: float,
        buy_fraction: float,
    ) -> int:
        available_cash = (
            portfolio.cash
            * buy_fraction
        )

        return int(
            available_cash // price
        )


    def _calculate_sell_quantity(
        self,
        portfolio: Portfolio,
        sell_fraction: float,
    ) -> int:
        return int(
            portfolio.position.quantity
            * sell_fraction
        )

    def _execute_equity_order(
        self,
        order: Order,
        price: float,
        timestamp,
        portfolio: Portfolio,
        trades: list,
    ) -> None:

        execution = self.executor.execute(
            order=order,
            price=price,
        )

        portfolio.apply_execution(
            execution
        )

        trades.append(
            Trade(
                timestamp=pd.Timestamp(
                    timestamp
                ),
                action=execution.order.action,
                quantity=execution.order.quantity,
                price=execution.execution_price,
            )
        )

    def _execute_option_order(
        self,
        order: OptionOrder,
        quote: ExecutableOptionQuote,
        portfolio: Portfolio,
    ) -> None:

        execution = self.option_executor.execute(
            order=order,
            quote=quote,
        )

        portfolio.apply_option_execution(
            execution
        )

    def _get_option_mark_prices(
        self,
        timestamp,
        portfolio: Portfolio,
        option_data_provider: HistoricalOptionDataProvider | None,
        last_option_prices: dict,
    ) -> dict:

        if not portfolio.option_positions:
            return {}

        if option_data_provider is None:
            raise ValueError(
                "option_data_provider is required "
                "to value option positions"
            )

        option_prices = {}

        for contract in portfolio.option_positions:

            try:
                quote = option_data_provider.get_quote(
                    timestamp=timestamp,
                    contract=contract,
                )

                mark_price = quote.bid

                last_option_prices[contract] = (
                    mark_price
                )

            except ValueError:

                if contract not in last_option_prices:
                    raise

                mark_price = last_option_prices[
                    contract
                ]

            option_prices[contract] = mark_price

        return option_prices

    def run(
        self,
        prices: pd.Series,
        strategy: BaseStrategy,
        portfolio: Portfolio,
        buy_fraction: float = 1.0,
        sell_fraction: float = 1.0,
        option_data_provider: HistoricalOptionDataProvider | None = None,
    ) -> BacktestResult:

        if not 0 < buy_fraction <= 1:
            raise ValueError(
                "buy_fraction must be greater than 0 and at most 1"
            )

        if not 0 < sell_fraction <= 1:
            raise ValueError(
                "sell_fraction must be greater than 0 and at most 1"
            )


        equity_curve = []
        trades = []
        last_option_prices = {}

        if hasattr(strategy, "generate_orders"):
            instructions = strategy.generate_orders(
                prices
            )
            explicit_orders = True
        else:
            instructions = strategy.generate(
                prices
            )
            explicit_orders = False

        if len(instructions) != len(prices):
            raise ValueError(
                "strategy output length must match price series length"
            )


        for timestamp, instruction, price in zip(
            prices.index,
            instructions,
            prices,
        ):
                if explicit_orders:

                    instruction = instruction

                    if instruction is not None:

                        if isinstance(
                            instruction,
                            (
                                OptionOrder,
                                OptionOrderIntent,
                            ),
                        ):

                            if option_data_provider is None:
                                raise ValueError(
                                    "option_data_provider is required "
                                    "for option instructions"
                                )

                            quote = option_data_provider.get_quote(
                                timestamp=timestamp,
                                contract=instruction.contract,
                            )

                            order = (
                                self.option_instruction_resolver.resolve(
                                    instruction=instruction,
                                    quote=quote,
                                    cash=portfolio.cash,
                                )
                            )

                            if order is not None:
                                self._execute_option_order(
                                    order=order,
                                    quote=quote,
                                    portfolio=portfolio,
                                )

                        else:

                            self._execute_equity_order(
                                order=instruction,
                                price=price,
                                timestamp=timestamp,
                                portfolio=portfolio,
                                trades=trades,
                            )
                else:
                    if isinstance(
                        instruction,
                        EquityOrderIntent,
                    ):

                        order = (
                            self.equity_instruction_resolver.resolve(
                                instruction=instruction,
                                price=price,
                                cash=portfolio.cash,
                            )
                        )

                        if order is not None:

                            self._execute_equity_order(
                                order=order,
                                price=price,
                                timestamp=timestamp,
                                portfolio=portfolio,
                                trades=trades,
                            )

                    else:

                        signal = instruction

                        if signal == Signal.BUY:

                            quantity = self._calculate_buy_quantity(
                                portfolio=portfolio,
                                price=price,
                                buy_fraction=buy_fraction,
                            )

                            if quantity > 0:

                                order = Order(
                                    action=Signal.BUY,
                                    quantity=quantity,
                                )

                                self._execute_equity_order(
                                    order=order,
                                    price=price,
                                    timestamp=timestamp,
                                    portfolio=portfolio,
                                    trades=trades,
                                )

                        elif signal == Signal.SELL:

                            if portfolio.position.quantity > 0:

                                quantity = self._calculate_sell_quantity(
                                    portfolio=portfolio,
                                    sell_fraction=sell_fraction,
                                )

                                if quantity > 0:

                                    order = Order(
                                        action=Signal.SELL,
                                        quantity=quantity,
                                    )

                                    self._execute_equity_order(
                                        order=order,
                                        price=price,
                                        timestamp=timestamp,
                                        portfolio=portfolio,
                                        trades=trades,
                                    )

                option_prices = self._get_option_mark_prices(
                    timestamp=timestamp,
                    portfolio=portfolio,
                    option_data_provider=option_data_provider,
                    last_option_prices=last_option_prices,
                )

                equity = portfolio.total_equity(
                    price=price,
                    option_prices=option_prices,
                )

                equity_curve.append(
                    equity
                )

        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades,
            portfolio=portfolio,
        )