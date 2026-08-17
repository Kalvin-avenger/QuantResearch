import pandas as pd
import pytest

from quantresearch.backtest.engine import (
    BacktestEngine,
)
from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)
from quantresearch.data.historical_options import (
    HistoricalOptionQuoteStore,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.portfolio import Portfolio
from quantresearch.strategy.spy_leaps_ladder import (
    SpyLeapsLadderStrategy,
)


def test_spy_leaps_ladder_initial_allocation_end_to_end():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2027-12-17"
        ),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    prices = pd.Series(
        [
            500.0,
            505.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-05 15:59:00"
            ),
            bid=26.0,
            ask=27.0,
        ),
    ]

    store = (
        HistoricalOptionQuoteStore
        .from_historical_quotes(
            quotes
        )
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    assert portfolio.position.quantity == 50

    assert contract in portfolio.option_positions

    option_position = (
        portfolio.option_positions[
            contract
        ]
    )

    assert option_position.quantity == 10

    assert portfolio.cash == pytest.approx(
        50000.0
    )

    assert len(result.trades) == 1

    assert result.equity_curve[0] == pytest.approx(
        99000.0
    )
    assert result.equity_curve[1] == pytest.approx(
        101250.0
    )

def test_spy_leaps_ladder_dynamic_drawdown_end_to_end():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
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

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-05 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-06 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
    ]

    store = (
        HistoricalOptionQuoteStore
        .from_historical_quotes(
            quotes
        )
    )

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        drawdown_step=0.05,
        max_tranches=2,
    )

    engine = BacktestEngine()

    engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    # -----------------------------------------
    # Initial tranche:
    #
    # $25,000 / $500
    # = 50 shares
    # -----------------------------------------

    # -----------------------------------------
    # -5% tranche:
    #
    # $25,000 / $475
    # = 52 shares
    # -----------------------------------------

    assert portfolio.position.quantity == 102

    option_position = (
        portfolio.option_positions[
            contract
        ]
    )

    # Each tranche:
    #
    # $25,000 /
    # ($25 × 100)
    # = 10 contracts

    assert option_position.quantity == 20

    # Initial:
    #
    # SPY      25,000
    # options  25,000
    #
    # cash = 50,000
    #
    # Second tranche:
    #
    # SPY:
    # 52 × 475 = 24,700
    #
    # options:
    # 10 × 25 × 100 = 25,000
    #
    # ending cash = 300

    assert portfolio.cash == pytest.approx(
        300.0
    )

    assert strategy.tranches_deployed == 2


def test_spy_leaps_ladder_take_profit_end_to_end():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    prices = pd.Series(
        [
            500.0,
            505.0,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
        ],
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-05 15:59:00"
            ),
            bid=32.0,
            ask=33.0,
        ),
    ]

    store = (
        HistoricalOptionQuoteStore
        .from_historical_quotes(
            quotes
        )
    )

    portfolio = Portfolio(
        initial_cash=100000.0,
    )

    strategy = SpyLeapsLadderStrategy(
        leaps_contract=contract,
        equity_allocation=0.25,
        option_allocation=0.25,
        take_profit_threshold=0.25,
        max_tranches=2,
    )

    engine = BacktestEngine()

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_data_provider=store,
    )

    option_position = (
        portfolio.option_positions[
            contract
        ]
    )

    assert contract not in portfolio.option_positions

    assert portfolio.position.quantity == 50

    assert portfolio.cash == pytest.approx(
        82000.0
    )

    assert option_position.realized_pnl == pytest.approx(
        7000.0
    )

    assert result.equity_curve[-1] == pytest.approx(
        107250.0
    )

