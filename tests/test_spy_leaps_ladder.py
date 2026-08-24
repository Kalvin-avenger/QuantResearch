import pandas as pd
import pytest

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.strategy.spy_leaps_ladder import (
    SpyLeapsLadderStrategy,
)

from quantresearch.strategy.context import (
    StrategyContext,
)

from quantresearch.accounting.option_position import (
    OptionPosition,
)

from quantresearch.orders.option_order import (
    OptionOrder,
)

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)

from quantresearch.signals import Signal

from quantresearch.orders.option_order_intent import (
    OptionOrderIntent,
)

from quantresearch.orders.equity_order_intent import (
    EquityOrderIntent,
)

from quantresearch.strategy.leaps_contract_resolver import (
    FixedLeapsContractResolver,
)

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



def test_spy_leaps_ladder_initial_allocations():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    assert strategy.equity_allocation == pytest.approx(
        0.25
    )

    assert strategy.option_allocation == pytest.approx(
        0.25
    )

    assert strategy.leaps_contract == contract

def test_spy_leaps_ladder_generates_initial_orders():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    instructions = strategy.generate_initial_instructions()

    assert len(instructions) == 2

    equity_instruction = instructions[0]
    option_instruction = instructions[1]

    assert equity_instruction.allocation_fraction == pytest.approx(
        0.25
    )

    assert option_instruction.allocation_fraction == pytest.approx(
        0.25
    )

    assert option_instruction.contract == contract

def test_spy_leaps_ladder_calculates_drawdown():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    drawdown = strategy.calculate_drawdown(
        price=475.0,
        peak_price=500.0,
    )

    assert drawdown == pytest.approx(
        -0.05
    )

@pytest.mark.parametrize(
    "price, expected_level",
    [
        (500.0, 0),
        (490.0, 0),
        (475.0, 1),
        (460.0, 1),
        (450.0, 2),
        (425.0, 3),
    ],
)

def test_spy_leaps_ladder_drawdown_levels(
    price,
    expected_level,
):

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    level = strategy.drawdown_level(
        price=price,
        peak_price=500.0,
    )

    assert level == expected_level

def test_drawdown_level_triggers_only_once():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    prices = [
        500.0,
        480.0,
        475.0,
        470.0,
        455.0,
        450.0,
        460.0,
    ]

    triggers = [
        strategy.update_drawdown_state(price)
        for price in prices
    ]

    assert triggers == [
        None,
        None,
        1,
        None,
        None,
        2,
        None,
    ]

def test_new_peak_resets_drawdown_ladder():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    assert strategy.update_drawdown_state(
        500.0
    ) is None

    assert strategy.update_drawdown_state(
        475.0
    ) == 1

    assert strategy.update_drawdown_state(
        510.0
    ) is None

    assert strategy.peak_price == pytest.approx(
        510.0
    )

    assert strategy.last_triggered_level == 0

    assert strategy.update_drawdown_state(
        484.5
    ) == 1

def test_generate_orders_adds_tranche_on_drawdown_levels():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    prices = pd.Series(
        [
            500.0,
            480.0,
            475.0,
            470.0,
            450.0,
        ],
        index=pd.date_range(
            "2026-01-02",
            periods=5,
            freq="B",
        ),
    )

    orders = strategy.generate_orders(
        prices
    )

    assert orders[0] is not None
    assert orders[1] is None
    assert orders[2] is not None
    assert orders[3] is None
    assert orders[4] is not None

    assert len(orders[0]) == 2
    assert len(orders[2]) == 2
    assert len(orders[4]) == 2

def test_drawdown_tranches_use_configured_allocations():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.20,
        option_allocation=0.15,
        drawdown_step=0.05,
        max_tranches=3,
    )
    prices = pd.Series(
        [
            500.0,
            475.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    orders = strategy.generate_orders(
        prices
    )

    drawdown_orders = orders[1]

    equity_intent = drawdown_orders[0]
    option_intent = drawdown_orders[1]

    assert equity_intent.allocation_fraction == pytest.approx(
        0.20
    )

    assert option_intent.allocation_fraction == pytest.approx(
        0.15
    )

def test_ladder_tranches_use_fixed_initial_capital():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        initial_capital=100000.0,
        max_tranches=3,
    )

    prices = pd.Series(
        [
            500.0,
            475.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    orders = strategy.generate_orders(
        prices
    )

    initial_orders = orders[0]
    drawdown_orders = orders[1]

    assert initial_orders[0].allocation_base == pytest.approx(
        100000.0
    )
    assert initial_orders[1].allocation_base == pytest.approx(
        100000.0
    )

    assert drawdown_orders[0].allocation_base == pytest.approx(
        100000.0
    )
    assert drawdown_orders[1].allocation_base == pytest.approx(
        100000.0
    )

def test_ladder_respects_max_tranches():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        initial_capital=100000.0,
        max_tranches=2,
    )

    prices = pd.Series(
        [
            500.0,
            475.0,
            450.0,
            425.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
            pd.Timestamp("2026-01-07"),
        ],
    )

    orders = strategy.generate_orders(
        prices
    )

    assert orders[0] is not None
    assert orders[1] is not None

    assert orders[2] is None
    assert orders[3] is None

    assert strategy.active_equity_tranches == 2

def test_ladder_can_support_more_tranches_when_configured():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=3,
    )

    prices = pd.Series(
        [
            500.0,
            475.0,
            450.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
        ],
    )

    orders = strategy.generate_orders(
        prices
    )

    assert orders[0] is not None
    assert orders[1] is not None
    assert orders[2] is not None

    assert strategy.active_equity_tranches == 3

def test_calculate_option_return():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        take_profit_threshold=0.25,
    )

    option_return = (
        strategy.calculate_option_return(
            current_bid=31.25,
            average_cost=25.0,
        )
    )

    assert option_return == pytest.approx(
        0.25
    )

@pytest.mark.parametrize(
    "current_bid, expected",
    [
        (24.0, False),
        (30.0, False),
        (31.24, False),
        (31.25, True),
        (32.0, True),
        (40.0, True),
    ],
)

def test_should_take_profit(
    current_bid,
    expected,
):

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        take_profit_threshold=0.25,
    )

    result = strategy.should_take_profit(
        current_bid=current_bid,
        average_cost=25.0,
    )

    assert result is expected

def test_option_return_rejects_non_positive_average_cost():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
    )

    with pytest.raises(
        ValueError,
        match="average_cost must be positive",
    ):
        strategy.calculate_option_return(
            current_bid=30.0,
            average_cost=0.0,
        )

def test_on_bar_generates_initial_tranche():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=2,
    )

    context = StrategyContext(
        cash=100000.0,
        option_positions={},
        option_quotes={},
    )

    instructions = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    assert instructions is not None
    assert len(instructions) == 2

    assert strategy.initial_capital == pytest.approx(
        100000.0
    )

    assert strategy.peak_price == pytest.approx(
        500.0
    )

    assert strategy.active_equity_tranches == 1

    assert instructions[0].allocation_base == pytest.approx(
        100000.0
    )

    assert instructions[1].allocation_base == pytest.approx(
        100000.0
    )

def test_on_bar_adds_tranche_at_drawdown():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=2,
    )

    context = StrategyContext(
        cash=100000.0,
        option_positions={},
        option_quotes={},
    )

    first = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    second = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-05"),
        price=480.0,
        context=context,
    )

    third = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-06"),
        price=475.0,
        context=context,
    )

    fourth = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-07"),
        price=450.0,
        context=context,
    )

    assert first is not None

    assert second is None

    assert third is not None
    assert len(third) == 2

    # max_tranches=2, so -10% cannot
    # deploy another tranche.
    assert fourth is None

    assert strategy.active_equity_tranches == 2

def test_on_bar_generates_option_sell_at_take_profit():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        take_profit_threshold=0.25,
    )

    position = OptionPosition(
        contract=contract,
        quantity=10,
        average_cost=25.0,
    )

    quote = HistoricalOptionQuote(
        contract=contract,
        timestamp=pd.Timestamp(
            "2026-01-05 15:59:00"
        ),
        bid=32.0,
        ask=33.0,
    )

    context = StrategyContext(
        cash=50000.0,
        option_positions={
            contract: position,
        },
        option_quotes={
            contract: quote,
        },
    )

    # Established market state.
    strategy.peak_price = 500.0

    # IMPORTANT:
    # Take-profit now operates from the tranche
    # lifecycle ledger rather than self.leaps_contract.
    tranche = strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract,
    )

    orders = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-05"),
        price=505.0,
        context=context,
    )

    order = assert_single_option_sell(
        orders
    )

    assert order.contract == contract
    assert order.quantity == 10

    # Take-profit closes the matching
    # option lifecycle state.
    assert tranche.option_deployed is False
    assert tranche.option_closed is True

    # Equity exposure remains active.
    assert tranche.equity_deployed is True

def test_strategy_starts_with_no_tranche_states():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
    )

    assert strategy.tranches == []


def test_initial_runtime_bar_creates_first_tranche_state():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
    )

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=FakeContext(),
    )

    assert len(strategy.tranches) == 1

    tranche = strategy.tranches[0]

    assert tranche.level == 0
    assert tranche.equity_deployed is True
    assert tranche.option_deployed is True
    assert tranche.option_closed is False

def test_drawdown_runtime_bar_creates_second_tranche_state():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        drawdown_step=0.05,
    )

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    # Initial deployment.
    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    # 5% drawdown from the 500 peak.
    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=475.0,
        context=context,
    )

    assert len(strategy.tranches) == 2

    first_tranche = strategy.tranches[0]
    second_tranche = strategy.tranches[1]

    assert first_tranche.level == 0
    assert second_tranche.level == 1

    assert second_tranche.equity_deployed is True
    assert second_tranche.option_deployed is True
    assert second_tranche.option_closed is False

def test_take_profit_closes_option_leg_for_all_deployed_tranches():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        drawdown_step=0.05,
        max_tranches=2,
        take_profit_threshold=0.25,
    )

    class FakePosition:
        quantity = 4
        average_cost = 10.0

    class FakeQuote:
        bid = 13.0

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    # Initial tranche.
    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    # Second tranche at 5% drawdown.
    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=475.0,
        context=context,
    )

    assert len(strategy.tranches) == 2

    assert strategy.tranches[0].option_deployed is True
    assert strategy.tranches[1].option_deployed is True

    # Simulate the aggregated option position
    # after both tranches have been executed.
    context.option_positions = {
        contract: FakePosition(),
    }

    context.option_quotes = {
        contract: FakeQuote(),
    }

    orders = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-04"),
        price=480.0,
        context=context,
    )

    order = assert_single_option_sell(
        orders
    )

    assert order.quantity == 4

    assert strategy.tranches[0].equity_deployed is True
    assert strategy.tranches[1].equity_deployed is True

    assert strategy.tranches[0].option_deployed is False
    assert strategy.tranches[1].option_deployed is False

    assert strategy.tranches[0].option_closed is True
    assert strategy.tranches[1].option_closed is True

    # Equity tranches are still deployed.
    assert strategy.active_equity_tranches == 2

def test_option_leg_remains_open_when_take_profit_not_reached():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        take_profit_threshold=0.25,
    )

    class FakePosition:
        quantity = 2
        average_cost = 10.0

    class FakeQuote:
        bid = 12.0

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    context.option_positions = {
        contract: FakePosition(),
    }

    context.option_quotes = {
        contract: FakeQuote(),
    }

    order = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=500.0,
        context=context,
    )

    assert order is None

    tranche = strategy.tranches[0]

    assert tranche.equity_deployed is True
    assert tranche.option_deployed is True
    assert tranche.option_closed is False

    assert strategy.active_equity_tranches == 1

def test_active_tranche_counts_after_two_deployments():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        drawdown_step=0.05,
        max_tranches=2,
    )

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    # Initial tranche.
    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    # Second tranche.
    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=475.0,
        context=context,
    )

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 2

def test_option_capacity_is_released_after_take_profit():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        drawdown_step=0.05,
        max_tranches=2,
    )

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=475.0,
        context=context,
    )

    strategy.close_deployed_option_legs()

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 0

    # SPY exposure still exists even though
    # the option legs have been closed.
    assert strategy.active_equity_tranches == 2

def test_deeper_drawdown_recycles_option_only_after_take_profit():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        drawdown_step=0.05,
        max_tranches=2,
        take_profit_threshold=0.25,
    )

    class FakePosition:
        quantity = 4
        average_cost = 10.0

    class FakeQuote:
        bid = 13.0

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    # -----------------------------------------
    # Tranche 0
    # -----------------------------------------

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    # -----------------------------------------
    # Tranche 1 at -5%
    # -----------------------------------------

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=475.0,
        context=context,
    )

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 2

    # -----------------------------------------
    # LEAPS take-profit
    # -----------------------------------------

    context.option_positions = {
        contract: FakePosition(),
    }

    context.option_quotes = {
        contract: FakeQuote(),
    }

    sell_orders = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-04"),
        price=480.0,
        context=context,
    )

    sell_order = assert_single_option_sell(
        sell_orders
    )

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 0

    # Simulate execution:
    # the option position has now been sold.
    context.option_positions = {}
    context.option_quotes = {}

    # -----------------------------------------
    # New deeper drawdown: -10%
    # -----------------------------------------

    instructions = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-05"),
        price=450.0,
        context=context,
    )

    assert instructions is not None
    assert len(instructions) == 1

    instruction = instructions[0]

    assert isinstance(
        instruction,
        OptionOrderIntent,
    )

    assert instruction.action == Signal.BUY
    assert instruction.contract == contract

    # SPY exposure remains capped.
    assert strategy.active_equity_tranches == 2

    # One recycled LEAPS tranche is now active.
    assert strategy.active_option_tranches == 1

    assert strategy.active_equity_tranches == 2

def test_option_only_recycling_does_not_increase_equity_tranche_count():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        max_tranches=2,
    )

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=475.0,
        context=context,
    )

    assert strategy.active_equity_tranches == 2

    strategy.close_deployed_option_legs()

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-04"),
        price=450.0,
        context=context,
    )

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 1

def test_take_profit_bar_updates_new_peak():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        take_profit_threshold=0.25,
    )

    class FakePosition:
        quantity = 2
        average_cost = 10.0

    class FakeQuote:
        bid = 13.0

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    # Initial peak.
    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    assert strategy.peak_price == 500.0

    # LEAPS reaches take profit on the same bar
    # that SPY makes a new high.
    context.option_positions = {
        contract: FakePosition(),
    }

    context.option_quotes = {
        contract: FakeQuote(),
    }

    orders = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=550.0,
        context=context,
    )

    order = assert_single_option_sell(
        orders
    )

    # assert isinstance(
    #     order,
    #     OptionOrder,
    # )

    # assert order.action == Signal.SELL

    # Market state must still advance even though
    # the strategy returned a take-profit order.
    assert strategy.peak_price == 550.0
    assert strategy.last_triggered_level == 0

def test_multiple_take_profit_and_recycling_cycles():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        drawdown_step=0.05,
        max_tranches=2,
        take_profit_threshold=0.25,
    )

    class FakePosition:
        def __init__(
            self,
            quantity,
            average_cost,
        ):
            self.quantity = quantity
            self.average_cost = average_cost

    class FakeQuote:
        def __init__(
            self,
            bid,
        ):
            self.bid = bid

    class FakeContext:
        cash = 100000.0
        option_positions = {}
        option_quotes = {}

    context = FakeContext()

    # =====================================================
    # 1. Initial deployment at 500
    # =====================================================

    initial_orders = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=500.0,
        context=context,
    )

    assert len(initial_orders) == 2

    assert strategy.active_equity_tranches == 1
    assert strategy.active_option_tranches == 1
    assert strategy.peak_price == 500.0

    # =====================================================
    # 2. New high at 550 + LEAPS take-profit
    # =====================================================

    context.option_positions = {
        contract: FakePosition(
            quantity=2,
            average_cost=10.0,
        ),
    }

    context.option_quotes = {
        contract: FakeQuote(
            bid=13.0,
        ),
    }

    first_sell_orders = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-03"),
        price=550.0,
        context=context,
    )

    first_sell = assert_single_option_sell(
        first_sell_orders
    )

    assert first_sell.action == Signal.SELL

    assert strategy.peak_price == 550.0

    assert strategy.active_equity_tranches == 1
    assert strategy.active_option_tranches == 0

    # Simulate completed sale.
    context.option_positions = {}
    context.option_quotes = {}

    # =====================================================
    # 3. 5% drawdown from the new 550 peak
    # =====================================================

    recycled_orders = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-04"),
        price=522.5,
        context=context,
    )

    assert recycled_orders is not None

    # Equity still has available capacity because
    # only one equity tranche currently exists.
    assert len(recycled_orders) == 2

    assert isinstance(
        recycled_orders[0],
        EquityOrderIntent,
    )

    assert isinstance(
        recycled_orders[1],
        OptionOrderIntent,
    )

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 1

    # =====================================================
    # 4. Recycled LEAPS reaches take-profit again
    # =====================================================

    context.option_positions = {
        contract: FakePosition(
            quantity=2,
            average_cost=10.0,
        ),
    }

    context.option_quotes = {
        contract: FakeQuote(
            bid=13.0,
        ),
    }

    second_sell_orders = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-05"),
        price=520.0,
        context=context,
    )

    second_sell = assert_single_option_sell(
        second_sell_orders
    )

    assert second_sell.action == Signal.SELL

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 0

    context.option_positions = {}
    context.option_quotes = {}

    # =====================================================
    # 5. 10% drawdown from 550
    # =====================================================

    second_recycle = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-06"),
        price=495.0,
        context=context,
    )

    assert second_recycle is not None

    # Equity capacity is already full.
    # Only LEAPS should be recycled.
    assert len(second_recycle) == 1

    assert isinstance(
        second_recycle[0],
        OptionOrderIntent,
    )

    assert second_recycle[0].action == Signal.BUY

    # =====================================================
    # Final state
    # =====================================================

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 1

    assert strategy.peak_price == 550.0
    assert strategy.last_triggered_level == 2

def test_max_tranches_does_not_limit_lifetime_option_recycling():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        max_tranches=2,
    )

    strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
    )

    strategy.create_tranche(
        level=1,
        deploy_equity=True,
        deploy_option=True,
    )

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 2

    strategy.close_deployed_option_legs()

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 0

    # Historical tranche objects remain.
    assert len(strategy.tranches) == 2

    # But option capacity has been released.
    assert strategy.active_option_tranches < strategy.max_tranches

def test_active_equity_tranches_is_derived_from_tranche_state():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
        max_tranches=2,
    )

    assert strategy.active_equity_tranches == 0

    strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
    )

    assert strategy.active_equity_tranches == 1

    strategy.create_tranche(
        level=1,
        deploy_equity=True,
        deploy_option=True,
    )

    assert strategy.active_equity_tranches == 2

    strategy.close_deployed_option_legs()

    # Closing LEAPS does not affect equity deployment.
    assert strategy.active_equity_tranches == 2

def test_active_equity_tranches_counts_equity_legs_not_history():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        initial_capital=100000.0,
    )

    strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
    )

    strategy.create_tranche(
        level=1,
        deploy_equity=True,
        deploy_option=True,
    )

    # Historical recycled option-only tranche.
    strategy.create_tranche(
        level=2,
        deploy_equity=False,
        deploy_option=True,
    )

    assert len(strategy.tranches) == 3

    assert strategy.active_equity_tranches == 2
    # assert strategy.active_equity_tranches == 2

def test_strategy_wraps_legacy_contract_with_fixed_resolver():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
    )

    assert isinstance(
        strategy.contract_resolver,
        FixedLeapsContractResolver,
    )

    resolved = strategy.contract_resolver.resolve(
        timestamp=pd.Timestamp("2026-01-02"),
        underlying_price=500.0,
    )

    assert resolved == contract

def test_strategy_accepts_explicit_contract_resolver():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    resolver = FixedLeapsContractResolver(
        contract=contract,
    )

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
    )

    assert strategy.contract_resolver is resolver

def test_strategy_requires_contract_or_resolver():

    with pytest.raises(
        ValueError,
        match="Either leaps_contract or contract_resolver must be provided",
    ):
        SpyLeapsLadderStrategy()

def test_runtime_tranche_records_resolved_option_contract():

    legacy_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    resolved_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-01-21"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    class FakeResolver:

        def resolve(
            self,
            timestamp,
            underlying_price: float,
        ):
            return resolved_contract

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=legacy_contract,
        contract_resolver=FakeResolver(),
        initial_capital=100000.0,
    )

    context = StrategyContext(
        cash=100000.0,
        option_positions={},
        option_quotes={},
    )

    instructions = strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=503.0,
        context=context,
    )

    assert len(strategy.tranches) == 1

    tranche = strategy.tranches[0]

    assert (
        tranche.option_contract
        == resolved_contract
    )

    assert (
        instructions[1].contract
        == tranche.option_contract
    )

def test_runtime_deployment_resolves_contract_once():

    calls = []

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2028-01-21"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    class RecordingResolver:

        def resolve(
            self,
            timestamp,
            underlying_price: float,
        ):

            calls.append(
                (
                    timestamp,
                    underlying_price,
                )
            )

            return contract

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=RecordingResolver(),
        initial_capital=100000.0,
    )

    context = StrategyContext(
        cash=100000.0,
        option_positions={},
        option_quotes={},
    )

    strategy.on_bar(
        timestamp=pd.Timestamp("2026-01-02"),
        price=503.0,
        context=context,
    )

    assert len(calls) == 1

def test_get_active_option_contracts_deduplicates_same_contract():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
    )

    strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract,
    )

    strategy.create_tranche(
        level=1,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract,
    )

    contracts = (
        strategy.get_active_option_contracts()
    )

    assert contracts == [
        contract
    ]

def test_same_contract_across_multiple_tranches_generates_one_sell_order():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        take_profit_threshold=0.25,
    )

    strategy.create_tranche(
        level=0,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract,
    )

    strategy.create_tranche(
        level=1,
        deploy_equity=True,
        deploy_option=True,
        option_contract=contract,
    )

    class FakePosition:
        quantity = 4
        average_cost = 10.0

    class FakeQuote:
        bid = 13.0

    context = StrategyContext(
        cash=100000.0,
        option_positions={
            contract: FakePosition(),
        },
        option_quotes={
            contract: FakeQuote(),
        },
    )

    orders = (
        strategy.find_take_profit_orders(
            context=context,
        )
    )

    assert len(orders) == 1

    assert orders[0].contract == contract
    assert orders[0].quantity == 4