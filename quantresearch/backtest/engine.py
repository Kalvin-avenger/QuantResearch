import pandas as pd

from quantresearch.strategy import BaseStrategy
from quantresearch.strategy.context import StrategyContext

from quantresearch.execution import Executor, Trade
from quantresearch.orders import Order
from quantresearch.portfolio import Portfolio
from quantresearch.signals import Signal
from quantresearch.backtest import BacktestResult

from quantresearch.orders.option_order import (
    OptionOrder,
)
from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)
from quantresearch.orders.option_instruction_resolver import (
    OptionInstructionResolver,
)

from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)
from quantresearch.orders.equity_instruction_resolver import (
    EquityInstructionResolver,
)

from quantresearch.execution.option_execution import (
    OptionExecutor,
)
from quantresearch.execution.option_quote_protocol import (
    ExecutableOptionQuote,
)

from quantresearch.data.option_provider import (
    HistoricalOptionDataProvider,
)

from quantresearch.data.daily_option_pricing import (
    DailyOptionExecutionQuoteAdapter,
)


class BacktestEngine:
    """
    Simple backtest engine.

    Supported strategy interfaces
    -----------------------------
    1. generate(prices)
       Legacy Signal-based strategies.

    2. generate_orders(prices)
       Pre-generated explicit Order / Intent strategies.

    3. on_bar(timestamp, price, context)
       Dynamic runtime strategies that require access to
       current portfolio state and option quotes.

    Assumptions
    -----------
    - Single equity asset
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

    # =====================================================
    # Equity sizing
    # =====================================================

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

    # =====================================================
    # Equity execution
    # =====================================================

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

    # =====================================================
    # Option execution
    # =====================================================

    def _resolve_option_market_quote(
        self,
        timestamp,
        contract,
        option_data_provider=None,
        option_bar_provider=None,
        option_pricing_policy=None,
    ):
        # ---------------------------------------------
        # Existing quote-driven path
        # ---------------------------------------------
        if option_data_provider is not None:
            return option_data_provider.get_quote(
                timestamp=timestamp,
                contract=contract,
            )

        # ---------------------------------------------
        # Daily bar-driven path
        # ---------------------------------------------
        if option_bar_provider is not None:
            if option_pricing_policy is None:
                raise ValueError(
                    "option_pricing_policy is required "
                    "when option_bar_provider is used"
                )

            bar = option_bar_provider.get_bar(
                timestamp=timestamp,
                contract=contract,
            )

            pricing = (
                option_pricing_policy.get_pricing(
                    bar=bar,
                )
            )

            return DailyOptionExecutionQuoteAdapter(
                pricing=pricing,
            )

        raise ValueError(
            "option market data provider is required"
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

    # =====================================================
    # Option mark-to-market
    # =====================================================

    def _get_option_mark_prices(
        self,
        timestamp,
        portfolio: Portfolio,
        option_data_provider: (
            HistoricalOptionDataProvider
            | None
        ),
        last_option_prices: dict,
        option_bar_provider=None,
        option_pricing_policy=None,
    ) -> dict:

        if not portfolio.option_positions:
            return {}

        if (
            option_data_provider is None
            and option_bar_provider is None
        ):
            raise ValueError(
                "option market data provider is required "
                "to value option positions"
            )

        option_prices = {}

        for contract in portfolio.option_positions:

            try:

                quote = self._resolve_option_market_quote(
                    timestamp=timestamp,
                    contract=contract,
                    option_data_provider=(
                        option_data_provider
                    ),
                    option_bar_provider=(
                        option_bar_provider
                    ),
                    option_pricing_policy=(
                        option_pricing_policy
                    ),
                )

                mark_price = getattr(
                    quote,
                    "mark_price",
                    quote.bid,
                )

                last_option_prices[
                    contract
                ] = mark_price

            except ValueError:

                if contract not in last_option_prices:
                    raise

                mark_price = (
                    last_option_prices[
                        contract
                    ]
                )

            option_prices[
                contract
            ] = mark_price

        return option_prices

    # =====================================================
    # Runtime StrategyContext
    # =====================================================

    def _build_strategy_context(
        self,
        timestamp,
        portfolio: Portfolio,
        option_data_provider=None,
        option_bar_provider=None,
        option_pricing_policy=None,
    ) -> StrategyContext:

        option_quotes = {}

        if (
            option_data_provider is not None
            or option_bar_provider is not None
        ):
            for contract in portfolio.option_positions:

                try:
                    quote = (
                        self._resolve_option_market_quote(
                            timestamp=timestamp,
                            contract=contract,
                            option_data_provider=(
                                option_data_provider
                            ),
                            option_bar_provider=(
                                option_bar_provider
                            ),
                            option_pricing_policy=(
                                option_pricing_policy
                            ),
                        )
                    )

                    option_quotes[
                        contract
                    ] = quote

                except ValueError:
                    # Missing market data is allowed
                    # in runtime strategy context.
                    #
                    # Strategy may simply decide
                    # not to act.
                    pass

        return StrategyContext(
            cash=portfolio.cash,
            option_positions=dict(
                portfolio.option_positions
            ),
            option_quotes=option_quotes,
        )

    # =====================================================
    # Explicit instructions
    # =====================================================

    def _execute_explicit_instruction(
        self,
        instruction,
        price: float,
        timestamp,
        portfolio: Portfolio,
        trades: list,
        option_data_provider,
        allocation_cash: float,
        option_bar_provider=None,
        option_pricing_policy=None,
    ) -> None:

        # -------------------------------------------------
        # Option Order / OptionOrderIntent
        # -------------------------------------------------

        if isinstance(
            instruction,
            (
                OptionOrder,
                OptionOrderIntent,
            ),
        ):

            quote = self._resolve_option_market_quote(
                timestamp=timestamp,
                contract=instruction.contract,
                option_data_provider=option_data_provider,
                option_bar_provider=option_bar_provider,
                option_pricing_policy=option_pricing_policy,
            )

            order = (
                self.option_instruction_resolver.resolve(
                    instruction=instruction,
                    quote=quote,
                    cash=allocation_cash,
                )
            )

            if order is not None:

                self._execute_option_order(
                    order=order,
                    quote=quote,
                    portfolio=portfolio,
                )

        # -------------------------------------------------
        # EquityOrderIntent
        # -------------------------------------------------

        elif isinstance(
            instruction,
            EquityOrderIntent,
        ):

            order = (
                self.equity_instruction_resolver.resolve(
                    instruction=instruction,
                    price=price,
                    cash=allocation_cash,
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

        # -------------------------------------------------
        # Explicit equity Order
        # -------------------------------------------------

        elif isinstance(
            instruction,
            Order,
        ):

            self._execute_equity_order(
                order=instruction,
                price=price,
                timestamp=timestamp,
                portfolio=portfolio,
                trades=trades,
            )

        # -------------------------------------------------
        # Unsupported
        # -------------------------------------------------

        else:

            raise TypeError(
                "unsupported explicit "
                "instruction type: "
                f"{type(instruction)}"
            )

    # =====================================================
    # Main backtest
    # =====================================================

    def run(
        self,
        prices: pd.Series,
        strategy: BaseStrategy,
        portfolio: Portfolio,
        buy_fraction: float = 1.0,
        sell_fraction: float = 1.0,
        option_data_provider: (
            HistoricalOptionDataProvider
            | None
        ) = None,
        option_bar_provider=None,
        option_pricing_policy=None,
    ) -> BacktestResult:

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not 0 < buy_fraction <= 1:
            raise ValueError(
                "buy_fraction must be greater "
                "than 0 and at most 1"
            )

        if not 0 < sell_fraction <= 1:
            raise ValueError(
                "sell_fraction must be greater "
                "than 0 and at most 1"
            )

        equity_curve = []
        trades = []

        last_option_prices = {}

        # =================================================
        # Detect strategy interface
        # =================================================

        dynamic_strategy = hasattr(
            strategy,
            "on_bar",
        )

        if dynamic_strategy:

            instructions = None

            # on_bar() returns explicit Order / Intent
            # objects rather than legacy Signals.
            explicit_orders = True

        elif hasattr(
            strategy,
            "generate_orders",
        ):

            instructions = (
                strategy.generate_orders(
                    prices
                )
            )

            explicit_orders = True

        else:

            instructions = strategy.generate(
                prices
            )

            explicit_orders = False

        # -------------------------------------------------
        # Validate pre-generated strategy output
        # -------------------------------------------------

        if (
            not dynamic_strategy
            and len(instructions) != len(prices)
        ):

            raise ValueError(
                "strategy output length must "
                "match price series length"
            )

        # =================================================
        # Main loop
        # =================================================

        for index, (
            timestamp,
            price,
        ) in enumerate(
            prices.items()
        ):

            price = float(price)

            # ---------------------------------------------
            # Snapshot before today's executions.
            #
            # All same-day allocation intents receive
            # the same allocation cash base.
            # ---------------------------------------------

            daily_cash_snapshot = (
                portfolio.cash
            )

            # =============================================
            # Dynamic on_bar strategy
            # =============================================

            if dynamic_strategy:

                context = self._build_strategy_context(
                    timestamp=timestamp,
                    portfolio=portfolio,
                    option_data_provider=option_data_provider,
                    option_bar_provider=option_bar_provider,
                    option_pricing_policy=option_pricing_policy,
                )

                instruction = strategy.on_bar(
                    timestamp=timestamp,
                    price=price,
                    context=context,
                )

            # =============================================
            # Pre-generated strategy
            # =============================================

            else:

                if isinstance(
                    instructions,
                    pd.Series,
                ):
                    instruction = (
                        instructions.iloc[index]
                    )

                else:
                    instruction = (
                        instructions[index]
                    )

            # =============================================
            # Explicit Order / Intent path
            # =============================================

            if explicit_orders:

                if instruction is not None:

                    # -------------------------------------
                    # Support multiple instructions
                    # on the same trading day.
                    # -------------------------------------

                    if isinstance(
                        instruction,
                        (list, tuple),
                    ):

                        daily_instructions = (
                            instruction
                        )

                    else:

                        daily_instructions = [
                            instruction
                        ]

                    for daily_instruction in (
                        daily_instructions
                    ):

                        self._execute_explicit_instruction(
                            instruction=daily_instruction,
                            price=price,
                            timestamp=timestamp,
                            portfolio=portfolio,
                            trades=trades,
                            option_data_provider=option_data_provider,
                            option_bar_provider=option_bar_provider,
                            option_pricing_policy=option_pricing_policy,
                            allocation_cash=daily_cash_snapshot,
                        )

            # =============================================
            # Legacy Signal path
            # =============================================

            else:

                signal = instruction

                # -----------------------------------------
                # BUY
                # -----------------------------------------

                if signal == Signal.BUY:

                    quantity = (
                        self._calculate_buy_quantity(
                            portfolio=portfolio,
                            price=price,
                            buy_fraction=(
                                buy_fraction
                            ),
                        )
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

                # -----------------------------------------
                # SELL
                # -----------------------------------------

                elif signal == Signal.SELL:

                    if (
                        portfolio.position.quantity
                        > 0
                    ):

                        quantity = (
                            self._calculate_sell_quantity(
                                portfolio=portfolio,
                                sell_fraction=(
                                    sell_fraction
                                ),
                            )
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

            # =============================================
            # End-of-day option mark-to-market
            # =============================================

            option_prices = (
                self._get_option_mark_prices(
                    timestamp=timestamp,
                    portfolio=portfolio,
                    option_data_provider=(
                        option_data_provider
                    ),
                    option_bar_provider=(
                        option_bar_provider
                    ),
                    option_pricing_policy=(
                        option_pricing_policy
                    ),
                    last_option_prices=(
                        last_option_prices
                    ),
                )
            )

            # =============================================
            # End-of-day portfolio NAV
            # =============================================

            equity = (
                portfolio.total_equity(
                    price=price,
                    option_prices=option_prices,
                )
            )

            equity_curve.append(
                equity
            )

        # =================================================
        # Result
        # =================================================

        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades,
            portfolio=portfolio,
        )