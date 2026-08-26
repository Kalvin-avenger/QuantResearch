import pandas as pd

from quantresearch.instruments.options import (
    OptionType,
)

from quantresearch.strategy.context import (
    StrategyContext,
)

from quantresearch.strategy.spy_leaps_ladder import (
    SpyLeapsLadderStrategy,
)

from quantresearch.strategy.leaps_contract_resolver import (
    DynamicLeapsContractResolver,
)

from quantresearch.data.providers.massive_options import (
    MassiveOptionContractUniverseProvider,
)

from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)

from quantresearch.instruments.options import (
    OptionContract
)

from quantresearch.strategy.leaps_contract_resolver import (
    FixedLeapsContractResolver
)

from quantresearch.orders.option_order import (
    OptionOrder,
)

from quantresearch.signals import Signal

from quantresearch.backtest.engine import (
    BacktestEngine,
)

from quantresearch.portfolio import (
    Portfolio,
)

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)

from quantresearch.data.historical_options import (
    HistoricalOptionQuoteStore,
)

from quantresearch.backtest.engine import BacktestEngine

from quantresearch.data.daily_option_pricing import (
    DailyCloseOptionPricingPolicy,
)

from quantresearch.data.historical_option_bar import (
    HistoricalOptionBar,
)

from quantresearch.portfolio import Portfolio




def assert_single_option_sell(
    result,
):
    assert isinstance(
        result,
        list,
    )

    assert len(result) == 1

    order = result[0]

    assert isinstance(
        order,
        OptionOrder,
    )

    assert order.action == Signal.SELL

    return order

def test_spy_leaps_ladder_selects_dynamic_contract_from_massive_universe():

    # =====================================================
    # Fake Massive historical contract universe
    # =====================================================

    raw_contracts = [
        # Too short.
        {
            "underlying_ticker": "SPY",
            "expiration_date": "2026-06-19",
            "strike_price": 500.0,
            "contract_type": "call",
        },

        # Eligible expiration, but farther from ATM.
        {
            "underlying_ticker": "SPY",
            "expiration_date": "2027-04-16",
            "strike_price": 490.0,
            "contract_type": "call",
        },

        # Desired contract:
        # target DTE + nearest strike to SPY=503.
        {
            "underlying_ticker": "SPY",
            "expiration_date": "2027-04-16",
            "strike_price": 500.0,
            "contract_type": "call",
        },

        {
            "underlying_ticker": "SPY",
            "expiration_date": "2027-04-16",
            "strike_price": 510.0,
            "contract_type": "call",
        },

        # Eligible, but farther from target DTE.
        {
            "underlying_ticker": "SPY",
            "expiration_date": "2027-06-18",
            "strike_price": 500.0,
            "contract_type": "call",
        },

        # PUT should never be selected.
        {
            "underlying_ticker": "SPY",
            "expiration_date": "2027-04-16",
            "strike_price": 500.0,
            "contract_type": "put",
        },
    ]

    class FakeMassiveClient:

        def __init__(self):
            self.calls = []

        def get_option_contracts(
            self,
            underlying_ticker,
            as_of,
            expiration_date_gte=None,
            expiration_date_lte=None,
        ):

            self.calls.append(
                (
                    underlying_ticker,
                    as_of,
                )
            )

            return raw_contracts

    # =====================================================
    # Infrastructure
    # =====================================================

    client = FakeMassiveClient()

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=100000.0,
        equity_allocation=0.25,
        option_allocation=0.25,
    )

    context = StrategyContext(
        cash=100000.0,
        option_positions={},
        option_quotes={},
    )

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    # =====================================================
    # Runtime deployment
    # =====================================================

    instructions = strategy.on_bar(
        timestamp=timestamp,
        price=503.0,
        context=context,
    )

    # =====================================================
    # Assertions
    # =====================================================

    assert instructions is not None
    assert len(instructions) == 2

    option_instruction = instructions[1]

    assert isinstance(
        option_instruction,
        OptionOrderIntent,
    )

    selected_contract = (
        option_instruction.contract
    )

    assert selected_contract.underlying == "SPY"

    assert (
        selected_contract.option_type
        == OptionType.CALL
    )

    assert (
        selected_contract.expiration
        == pd.Timestamp("2027-04-16")
    )

    assert selected_contract.strike == 500.0

    # =====================================================
    # Tranche must record exact same contract
    # =====================================================

    assert len(strategy.tranches) == 1

    tranche = strategy.tranches[0]

    assert tranche.option_deployed is True

    assert (
        tranche.option_contract
        == selected_contract
    )

    # =====================================================
    # Historical timestamp propagated to provider
    # =====================================================

    assert client.calls == [
        (
            "SPY",
            timestamp,
        )
    ]

def test_recycled_option_deployment_can_rotate_to_new_contract():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    class RotatingResolver:

        def __init__(self):
            self.calls = []

        def resolve(
            self,
            timestamp,
            underlying_price: float,
        ):

            self.calls.append(
                (
                    pd.Timestamp(timestamp),
                    underlying_price,
                )
            )

            if pd.Timestamp(timestamp).year == 2026:
                return contract_a

            return contract_b

    resolver = RotatingResolver()

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=100000.0,
        drawdown_step=0.05,
        max_tranches=2,
        take_profit_threshold=0.25,
    )

    context = StrategyContext(
        cash=100000.0,
        option_positions={},
        option_quotes={},
    )

    # =====================================================
    # 1. Initial deployment
    # =====================================================

    initial_instructions = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    initial_option_instruction = (
        initial_instructions[1]
    )

    assert (
        initial_option_instruction.contract
        == contract_a
    )

    assert (
        strategy.tranches[0].option_contract
        == contract_a
    )

    # =====================================================
    # 2. Simulate Contract A being closed
    # =====================================================

    strategy.close_deployed_option_legs()

    assert (
        strategy.active_option_tranches
        == 0
    )

    # =====================================================
    # 3. Move peak forward into 2027
    # =====================================================

    strategy.on_bar(
        timestamp=pd.Timestamp("2027-01-04"),
        price=600.0,
        context=context,
    )

    assert (
        strategy.peak_price
        == 600.0
    )

    # =====================================================
    # 4. New 5% drawdown from new peak
    # =====================================================

    recycled_instructions = strategy.on_bar(
        timestamp=pd.Timestamp("2027-01-05"),
        price=570.0,
        context=context,
    )

    assert recycled_instructions is not None

    option_instructions = [
        instruction
        for instruction in recycled_instructions
        if isinstance(
            instruction,
            OptionOrderIntent,
        )
    ]

    assert len(option_instructions) == 1

    recycled_option_instruction = (
        option_instructions[0]
    )

    assert (
        recycled_option_instruction.contract
        == contract_b
    )

    # =====================================================
    # 5. Lifecycle ledger
    # =====================================================

    assert len(strategy.tranches) == 2

    old_tranche = strategy.tranches[0]
    new_tranche = strategy.tranches[1]

    assert (
        old_tranche.option_contract
        == contract_a
    )

    assert (
        old_tranche.option_deployed
        is False
    )

    assert (
        old_tranche.option_closed
        is True
    )

    assert (
        new_tranche.option_contract
        == contract_b
    )

    assert (
        new_tranche.option_deployed
        is True
    )

    assert (
        new_tranche.option_closed
        is False
    )

def test_get_active_option_contracts_returns_only_open_contracts():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=FixedLeapsContractResolver(
            contract_a
        ),
    )

    tranche_a = strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract_a,
    )

    strategy.create_tranche(
        level=1,
        deploy_equity=False,
        deploy_option=True,
        option_contract=contract_b,
    )

    tranche_a.close_option()

    assert (
        strategy.get_active_option_contracts()
        == [contract_b]
    )

def test_close_option_contract_closes_only_matching_contract():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=FixedLeapsContractResolver(
            contract_a
        ),
    )

    tranche_a = strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract_a,
    )

    tranche_b = strategy.create_tranche(
        level=1,
        deploy_equity=False,
        deploy_option=True,
        option_contract=contract_b,
    )

    strategy.close_option_contract(
        contract_a
    )

    assert tranche_a.option_deployed is False
    assert tranche_a.option_closed is True

    assert tranche_b.option_deployed is True
    assert tranche_b.option_closed is False

def test_find_take_profit_order_uses_active_dynamic_contract():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=FixedLeapsContractResolver(
            contract_a
        ),
        take_profit_threshold=0.25,
    )

    tranche_a = strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract_a,
    )

    strategy.create_tranche(
        level=1,
        deploy_equity=False,
        deploy_option=True,
        option_contract=contract_b,
    )

    # A is historical / already closed.
    tranche_a.close_option()

    class FakePosition:

        quantity = 3
        average_cost = 10.0

    class FakeQuote:

        bid = 13.0

    context = StrategyContext(
        cash=100000.0,
        option_positions={
            contract_b: FakePosition(),
        },
        option_quotes={
            contract_b: FakeQuote(),
        },
    )

    order = strategy.find_take_profit_order(
        context=context,
    )

    assert isinstance(
        order,
        OptionOrder,
    )

    assert order.contract == contract_b
    assert order.action == Signal.SELL
    assert order.quantity == 3

def test_on_bar_takes_profit_on_dynamic_rotated_contract():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=FixedLeapsContractResolver(
            contract_a
        ),
        initial_capital=100000.0,
        take_profit_threshold=0.25,
    )

    # We are already inside an established market state.
    strategy.peak_price = 600.0

    old_tranche = strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract_a,
    )

    old_tranche.close_option()

    active_tranche = strategy.create_tranche(
        level=1,
        deploy_equity=False,
        deploy_option=True,
        option_contract=contract_b,
    )

    class FakePosition:

        quantity = 2
        average_cost = 10.0

    class FakeQuote:

        bid = 13.0

    context = StrategyContext(
        cash=100000.0,
        option_positions={
            contract_b: FakePosition(),
        },
        option_quotes={
            contract_b: FakeQuote(),
        },
    )

    orders = strategy.on_bar(
        timestamp=pd.Timestamp("2027-01-06"),
        price=590.0,
        context=context,
    )

    order = assert_single_option_sell(
        orders
    )


    assert order.contract == contract_b
    assert order.action == Signal.SELL
    assert order.quantity == 2

    assert active_tranche.option_deployed is False
    assert active_tranche.option_closed is True

    # Historical contract remains untouched.
    assert old_tranche.option_contract == contract_a

def test_find_take_profit_orders_returns_multiple_contracts():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=FixedLeapsContractResolver(
            contract_a
        ),
        take_profit_threshold=0.25,
    )

    strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract_a,
    )

    strategy.create_tranche(
        level=1,
        deploy_equity=False,
        deploy_option=True,
        option_contract=contract_b,
    )

    class PositionA:
        quantity = 2
        average_cost = 10.0

    class PositionB:
        quantity = 3
        average_cost = 20.0

    class QuoteA:
        bid = 13.0

    class QuoteB:
        bid = 26.0

    context = StrategyContext(
        cash=100000.0,
        option_positions={
            contract_a: PositionA(),
            contract_b: PositionB(),
        },
        option_quotes={
            contract_a: QuoteA(),
            contract_b: QuoteB(),
        },
    )

    orders = strategy.find_take_profit_orders(
        context=context,
    )

    assert len(orders) == 2

    assert orders[0].contract == contract_a
    assert orders[0].quantity == 2
    assert orders[0].action == Signal.SELL

    assert orders[1].contract == contract_b
    assert orders[1].quantity == 3
    assert orders[1].action == Signal.SELL

def test_find_take_profit_orders_only_returns_profitable_contracts():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=FixedLeapsContractResolver(
            contract_a
        ),
        take_profit_threshold=0.25,
    )

    strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract_a,
    )

    strategy.create_tranche(
        level=1,
        deploy_equity=False,
        deploy_option=True,
        option_contract=contract_b,
    )

    class PositionA:
        quantity = 2
        average_cost = 10.0

    class PositionB:
        quantity = 3
        average_cost = 20.0

    class QuoteA:
        bid = 13.0   # +30%

    class QuoteB:
        bid = 23.0   # +15%

    context = StrategyContext(
        cash=100000.0,
        option_positions={
            contract_a: PositionA(),
            contract_b: PositionB(),
        },
        option_quotes={
            contract_a: QuoteA(),
            contract_b: QuoteB(),
        },
    )

    orders = strategy.find_take_profit_orders(
        context=context,
    )

    assert len(orders) == 1
    assert orders[0].contract == contract_a

def test_on_bar_returns_multiple_take_profit_orders():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-04-21"),
        strike=550.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=FixedLeapsContractResolver(
            contract_a
        ),
        initial_capital=100000.0,
        take_profit_threshold=0.25,
    )

    strategy.peak_price = 600.0

    tranche_a = strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract_a,
    )

    tranche_b = strategy.create_tranche(
        level=1,
        deploy_equity=False,
        deploy_option=True,
        option_contract=contract_b,
    )

    class PositionA:
        quantity = 2
        average_cost = 10.0

    class PositionB:
        quantity = 3
        average_cost = 20.0

    class QuoteA:
        bid = 13.0

    class QuoteB:
        bid = 26.0

    context = StrategyContext(
        cash=100000.0,
        option_positions={
            contract_a: PositionA(),
            contract_b: PositionB(),
        },
        option_quotes={
            contract_a: QuoteA(),
            contract_b: QuoteB(),
        },
    )

    orders = strategy.on_bar(
        timestamp=pd.Timestamp("2027-01-06"),
        price=590.0,
        context=context,
    )

    assert isinstance(
        orders,
        list,
    )

    assert len(orders) == 2

    assert orders[0].contract == contract_a
    assert orders[1].contract == contract_b

    assert all(
        order.action == Signal.SELL
        for order in orders
    )

    assert tranche_a.option_deployed is False
    assert tranche_a.option_closed is True

    assert tranche_b.option_deployed is False
    assert tranche_b.option_closed is True

    assert strategy.active_option_tranches == 0

def test_spy_leaps_ladder_multi_contract_take_profit_end_to_end():

    contract_a = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_b = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-06-18"),
        strike=475.0,
        option_type=OptionType.CALL,
    )

    # =====================================================
    # Resolver:
    #
    # Initial deployment -> Contract A
    # First drawdown      -> Contract B
    # =====================================================

    class RotatingResolver:

        def resolve(
            self,
            timestamp,
            underlying_price: float,
        ):

            timestamp = pd.Timestamp(
                timestamp
            )

            if timestamp == pd.Timestamp(
                "2026-01-02"
            ):
                return contract_a

            return contract_b

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=RotatingResolver(),
        initial_capital=100000.0,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=2,
        take_profit_threshold=0.25,
    )

    # =====================================================
    # SPY path
    #
    # Day 1: 500
    #        initial tranche -> A
    #
    # Day 2: 475
    #        -5% drawdown
    #        second tranche -> B
    #
    # Day 3: 480
    #        both A and B exceed TP threshold
    # =====================================================

    prices = pd.Series(
        [
            500.0,
            475.0,
            480.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
        ],
    )

    # =====================================================
    # Option quotes
    #
    # Contract A:
    # Day 1 BUY at ask=25
    # Day 2 bid below TP
    # Day 3 bid=32 => +28%
    #
    # Contract B:
    # Day 2 BUY at ask=20
    # Day 3 bid=26 => +30%
    # =====================================================

    quotes = [
        HistoricalOptionQuote(
            contract=contract_a,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),

        HistoricalOptionQuote(
            contract=contract_a,
            timestamp=pd.Timestamp(
                "2026-01-05 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),

        HistoricalOptionQuote(
            contract=contract_a,
            timestamp=pd.Timestamp(
                "2026-01-06 15:59:00"
            ),
            bid=32.0,
            ask=33.0,
        ),

        HistoricalOptionQuote(
            contract=contract_b,
            timestamp=pd.Timestamp(
                "2026-01-05 15:59:00"
            ),
            bid=19.0,
            ask=20.0,
        ),

        HistoricalOptionQuote(
            contract=contract_b,
            timestamp=pd.Timestamp(
                "2026-01-06 15:59:00"
            ),
            bid=26.0,
            ask=27.0,
        ),
    ]

    option_store = (
        HistoricalOptionQuoteStore
        .from_historical_quotes(
            quotes
        )
    )

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    engine = BacktestEngine()

    # =====================================================
    # Run real strategy through real engine
    # =====================================================

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=option_store,
    )

    # =====================================================
    # Lifecycle ledger
    # =====================================================

    assert len(strategy.tranches) == 2

    tranche_a = strategy.tranches[0]
    tranche_b = strategy.tranches[1]

    assert (
        tranche_a.option_contract
        == contract_a
    )

    assert (
        tranche_b.option_contract
        == contract_b
    )

    # Both take-profit orders were generated
    # and lifecycle state was closed.

    assert tranche_a.option_deployed is False
    assert tranche_a.option_closed is True

    assert tranche_b.option_deployed is False
    assert tranche_b.option_closed is True

    assert (
        strategy.active_option_tranches
        == 0
    )

    # =====================================================
    # Portfolio execution
    # =====================================================

    assert (
        contract_a
        not in portfolio.option_positions
    )

    assert (
        contract_b
        not in portfolio.option_positions
    )

    assert portfolio.option_positions == {}

    # Equity legs remain deployed.

    assert (
        strategy.active_equity_tranches
        == 2
    )

    # Backtest completed normally.

    assert result.portfolio is portfolio

def test_spy_leaps_ladder_daily_bar_dynamic_leaps_end_to_end():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    # =====================================================
    # Dynamic contract universe
    # =====================================================

    resolver = DynamicLeapsContractResolver(
        contracts=[
            contract,
        ],
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=100000.0,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=1,
        take_profit_threshold=0.25,
    )

    # =====================================================
    # Two-day SPY path
    # =====================================================

    prices = pd.Series(
        [
            500.0,
            500.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    # =====================================================
    # Daily option bars
    #
    # Day 1:
    # close = 30
    #
    # Day 2:
    # close = 40
    #
    # Return = 40 / 30 - 1 = 33.3%
    # which is above 25% take-profit threshold.
    # =====================================================

    bars = {
        pd.Timestamp("2026-01-02"): HistoricalOptionBar(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-02"),
            open=29.0,
            high=31.0,
            low=28.0,
            close=30.0,
            volume=1000.0,
            vwap=29.8,
        ),
        pd.Timestamp("2026-01-05"): HistoricalOptionBar(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-05"),
            open=38.0,
            high=41.0,
            low=37.5,
            close=40.0,
            volume=1500.0,
            vwap=39.5,
        ),
    }

    class FakeOptionBarProvider:

        def __init__(self):
            self.calls = []

        def get_bar(
            self,
            timestamp,
            contract,
        ):
            timestamp = pd.Timestamp(
                timestamp
            )

            self.calls.append(
                (
                    timestamp,
                    contract,
                )
            )

            return bars[
                timestamp
            ]

    provider = FakeOptionBarProvider()

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_bar_provider=provider,
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    # =====================================================
    # Dynamic contract was actually used
    # =====================================================

    assert len(strategy.tranches) == 1

    tranche = strategy.tranches[0]

    assert tranche.option_contract == contract

    # =====================================================
    # Option should have been sold on Day 2
    # =====================================================

    assert contract not in portfolio.option_positions

    assert tranche.option_closed is True

    # =====================================================
    # Equity leg remains open
    # =====================================================

    assert portfolio.position.quantity == 50

    # =====================================================
    # Option realized PnL
    #
    # Option allocation = 25% of 100,000 = 25,000
    #
    # Contract cost:
    # 30 * 100 = 3,000
    #
    # Quantity:
    # floor(25,000 / 3,000) = 8
    #
    # Profit:
    # (40 - 30) * 8 * 100 = 8,000
    # =====================================================

    assert portfolio.realized_pnl == 8000.0

    # =====================================================
    # Final cash
    #
    # Initial:
    # 100,000
    #
    # Equity:
    # 50 * 500 = 25,000
    #
    # Option BUY:
    # 8 * 30 * 100 = 24,000
    #
    # Option SELL:
    # 8 * 40 * 100 = 32,000
    #
    # Final cash:
    # 100,000 - 25,000 - 24,000 + 32,000
    # = 83,000
    # =====================================================

    assert portfolio.cash == 83000.0

    # =====================================================
    # Final NAV
    #
    # cash = 83,000
    # equity = 50 * 500 = 25,000
    #
    # total = 108,000
    # =====================================================

    assert result.equity_curve[-1] == 108000.0

def test_daily_option_mark_to_market_uses_last_price_when_bar_missing():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-04-16"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    prices = pd.Series(
        [500.0, 500.0],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    first_bar = HistoricalOptionBar(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        open=29.0,
        high=31.0,
        low=28.0,
        close=30.0,
        volume=1000.0,
        vwap=29.8,
    )

    class FakeOptionBarProvider:

        def get_bar(
            self,
            timestamp,
            contract,
        ):
            timestamp = pd.Timestamp(timestamp)

            if timestamp == pd.Timestamp(
                "2026-01-02"
            ):
                return first_bar

            raise ValueError(
                "No historical option bar found"
            )

    class BuyOnceStrategy:

        def __init__(self):
            self.bought = False

        def on_bar(
            self,
            timestamp,
            price,
            context,
        ):
            if not self.bought:
                self.bought = True

                return OptionOrder(
                    contract=contract,
                    action=Signal.BUY,
                    quantity=1,
                )

            return None

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=BuyOnceStrategy(),
        portfolio=portfolio,
        option_bar_provider=FakeOptionBarProvider(),
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    assert contract in portfolio.option_positions

    position = portfolio.option_positions[
        contract
    ]

    assert position.quantity == 1
    assert position.average_cost == 30.0

    # Day 2 has no option bar, so MTM should
    # fall back to Day 1's last known price.
    #
    # Cash:
    # 100000 - 30 * 100 = 97000
    #
    # Option value:
    # 30 * 100 = 3000
    #
    # NAV:
    # 100000
    assert result.equity_curve[-1] == 100000.0