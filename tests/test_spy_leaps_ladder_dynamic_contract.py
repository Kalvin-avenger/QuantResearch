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

    order = strategy.on_bar(
        timestamp=pd.Timestamp("2027-01-06"),
        price=590.0,
        context=context,
    )

    assert isinstance(
        order,
        OptionOrder,
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