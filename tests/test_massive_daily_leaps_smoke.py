import os

import pandas as pd
import pytest

from quantresearch.data.providers.massive_options import (
    MassiveHistoricalOptionBarProvider,
    MassiveHttpClient,
    MassiveOptionContractUniverseProvider,
    format_massive_option_ticker,
)
from quantresearch.strategy.leaps_contract_resolver import (
    DynamicLeapsContractResolver,
)

from quantresearch.backtest.engine import BacktestEngine

from quantresearch.data.daily_option_pricing import (
    DailyCloseOptionPricingPolicy,
)

from quantresearch.portfolio import Portfolio

from quantresearch.strategy.spy_leaps_ladder import (
    SpyLeapsLadderStrategy,
)

from quantresearch.data.yahoo import (
    download_price_data,
)

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


@pytest.mark.integration
def test_massive_dynamic_leaps_daily_bar_smoke():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # -----------------------------------------------------
    # Historical SPY trading day.
    #
    # SPY traded around $680 on this date, so this is
    # sufficiently accurate for selecting the nearest
    # ATM LEAPS contract.
    # -----------------------------------------------------

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    underlying_price = 680.0

    # -----------------------------------------------------
    # Massive infrastructure
    # -----------------------------------------------------

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = (
        DynamicLeapsContractResolver(
            universe_provider=(
                universe_provider
            ),
            min_days_to_expiration=365,
            max_days_to_expiration=548,
            target_days_to_expiration=456,
        )
    )

    bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    # -----------------------------------------------------
    # Step 1:
    # Resolve a real historical LEAPS contract.
    # -----------------------------------------------------

    contract = resolver.resolve(
        timestamp=timestamp,
        underlying_price=underlying_price,
    )

    print(
        "\nResolved contract:",
        contract,
    )

    print(
        "Massive ticker:",
        format_massive_option_ticker(
            contract
        ),
    )

    # -----------------------------------------------------
    # Basic resolver sanity checks.
    # -----------------------------------------------------

    assert contract.underlying == "SPY"

    days_to_expiration = (
        pd.Timestamp(
            contract.expiration
        )
        - timestamp
    ).days

    assert (
        365
        <= days_to_expiration
        <= 548
    )

    # -----------------------------------------------------
    # Step 2:
    # Fetch the real daily aggregate bar.
    # -----------------------------------------------------

    bar = bar_provider.get_bar(
        timestamp=timestamp,
        contract=contract,
    )

    print(
        "Historical option bar:",
        bar,
    )

    # -----------------------------------------------------
    # Validate normalized daily data.
    # -----------------------------------------------------

    assert bar.contract == contract

    assert bar.open > 0
    assert bar.high > 0
    assert bar.low > 0
    assert bar.close > 0

    assert bar.high >= bar.low

    assert bar.high >= bar.open
    assert bar.high >= bar.close

    assert bar.low <= bar.open
    assert bar.low <= bar.close

@pytest.mark.integration
def test_massive_daily_leaps_engine_smoke():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # =====================================================
    # Historical test date
    # =====================================================

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    # We already confirmed in the previous live smoke test
    # that this produces a valid historical ATM LEAPS.
    underlying_price = 680.0

    prices = pd.Series(
        [underlying_price],
        index=[timestamp],
    )

    # =====================================================
    # Massive infrastructure
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = (
        DynamicLeapsContractResolver(
            universe_provider=(
                universe_provider
            ),
            min_days_to_expiration=365,
            max_days_to_expiration=548,
            target_days_to_expiration=456,
        )
    )

    option_bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    # =====================================================
    # Strategy
    # =====================================================

    initial_capital = 100000.0

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=initial_capital,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=1,
        take_profit_threshold=0.25,
    )

    portfolio = Portfolio(
        initial_cash=initial_capital,
    )

    engine = BacktestEngine()

    # =====================================================
    # Live one-day backtest
    # =====================================================

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_bar_provider=(
            option_bar_provider
        ),
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    # =====================================================
    # Strategy lifecycle
    # =====================================================

    assert len(strategy.tranches) == 1

    tranche = strategy.tranches[0]

    assert tranche.equity_deployed is True
    assert tranche.option_deployed is True
    assert tranche.option_closed is False

    contract = tranche.option_contract

    assert contract is not None
    assert contract.underlying == "SPY"

    print(
        "\nEngine resolved contract:",
        contract,
    )

    print(
        "Engine Massive ticker:",
        format_massive_option_ticker(
            contract
        ),
    )

    # =====================================================
    # Equity execution
    # =====================================================

    assert (
        portfolio.position.quantity
        > 0
    )

    print(
        "SPY quantity:",
        portfolio.position.quantity,
    )

    # =====================================================
    # Option execution
    # =====================================================

    assert contract in (
        portfolio.option_positions
    )

    option_position = (
        portfolio.option_positions[
            contract
        ]
    )

    assert option_position.quantity > 0
    assert option_position.average_cost > 0

    print(
        "Option quantity:",
        option_position.quantity,
    )

    print(
        "Option average cost:",
        option_position.average_cost,
    )

    # =====================================================
    # Cash accounting
    # =====================================================

    assert portfolio.cash < initial_capital
    assert portfolio.cash >= 0

    print(
        "Ending cash:",
        portfolio.cash,
    )

    # =====================================================
    # End-of-day NAV
    #
    # Because this is a one-day backtest:
    #
    # - equity executes at today's SPY price
    # - option executes at today's daily close
    # - option is marked at that same daily close
    #
    # With no commissions/slippage, NAV should therefore
    # remain equal to initial capital.
    # =====================================================

    assert len(result.equity_curve) == 1

    assert result.equity_curve[0] == pytest.approx(
        initial_capital
    )

    print(
        "Ending NAV:",
        result.equity_curve[0],
    )

@pytest.mark.integration
def test_massive_daily_leaps_five_day_backtest_smoke():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # =====================================================
    # Real SPY closes: Jan 2 -> Jan 8, 2026
    # =====================================================

    prices = pd.Series(
        [
            683.17,
            687.72,
            691.81,
            689.58,
            689.51,
        ],
        index=[
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-05"),
            pd.Timestamp("2026-01-06"),
            pd.Timestamp("2026-01-07"),
            pd.Timestamp("2026-01-08"),
        ],
    )

    # =====================================================
    # Massive infrastructure
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
    )

    option_bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    # =====================================================
    # Strategy / portfolio
    # =====================================================

    initial_capital = 100000.0

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=initial_capital,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=1,
        take_profit_threshold=0.25,
    )

    portfolio = Portfolio(
        initial_cash=initial_capital,
    )

    engine = BacktestEngine()

    # =====================================================
    # Run real five-day historical backtest
    # =====================================================

    preload_contract = resolver.resolve(
        timestamp=prices.index[0],
        underlying_price=float(
            prices.iloc[0]
        ),
    )

    print(
        "\nPreloaded contract:",
        preload_contract,
    )

    option_bar_provider.preload(
        contract=preload_contract,
        start_date=prices.index[0],
        end_date=prices.index[-1],
    )

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_bar_provider=option_bar_provider,
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    # =====================================================
    # Basic lifecycle validation
    # =====================================================

    assert len(result.equity_curve) == 5
    assert len(strategy.tranches) == 1

    tranche = strategy.tranches[0]

    assert tranche.option_contract is not None

    contract = tranche.option_contract

    assert contract.underlying == "SPY"

    print(
        "Resolved contract:",
        contract,
    )

    print(
        "Massive ticker:",
        format_massive_option_ticker(
            contract
        ),
    )

    assert tranche.equity_deployed is True
    assert tranche.option_deployed is True
    assert tranche.option_contract is not None

    

    print(
        "\nResolved contract:",
        contract,
    )

    print(
        "Massive ticker:",
        format_massive_option_ticker(
            contract
        ),
    )

    # =====================================================
    # Equity position
    # =====================================================

    assert portfolio.position.quantity > 0

    print(
        "SPY quantity:",
        portfolio.position.quantity,
    )

    # =====================================================
    # Option lifecycle
    #
    # Do NOT require the option to still be open.
    # A real price move could legitimately trigger TP.
    # =====================================================

    if contract in portfolio.option_positions:

        option_position = (
            portfolio.option_positions[
                contract
            ]
        )

        assert option_position.quantity > 0
        assert option_position.average_cost > 0

        print(
            "Option status: OPEN"
        )

        print(
            "Option quantity:",
            option_position.quantity,
        )

        print(
            "Option average cost:",
            option_position.average_cost,
        )

    else:

        assert tranche.option_closed is True

        print(
            "Option status: CLOSED"
        )

    # =====================================================
    # NAV curve
    # =====================================================

    assert all(
        equity > 0
        for equity in result.equity_curve
    )

    print(
        "NAV curve:"
    )

    for timestamp, nav in zip(
        prices.index,
        result.equity_curve,
    ):
        print(
            timestamp.date(),
            nav,
        )

    # =====================================================
    # Final accounting sanity
    # =====================================================

    assert portfolio.cash >= 0

    assert result.equity_curve[-1] > 0

    print(
        "Ending cash:",
        portfolio.cash,
    )

    print(
        "Ending NAV:",
        result.equity_curve[-1],
    )

def test_get_aggregate_bars_retries_on_429():
    class FakeResponse:
        def __init__(
            self,
            status_code,
            payload=None,
            headers=None,
        ):
            self.status_code = status_code
            self._payload = payload or {}
            self.headers = headers or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                import requests

                raise requests.HTTPError(
                    f"{self.status_code}"
                )

        def json(self):
            return self._payload

    class FakeSession:
        def __init__(self):
            self.calls = 0

        def get(
            self,
            url,
            params=None,
            headers=None,
        ):
            self.calls += 1

            if self.calls == 1:
                return FakeResponse(
                    status_code=429,
                    headers={
                        "Retry-After": "0",
                    },
                )

            return FakeResponse(
                status_code=200,
                payload={
                    "results": [
                        {
                            "o": 10,
                            "h": 12,
                            "l": 9,
                            "c": 11,
                            "t": 1,
                        }
                    ]
                },
            )

    session = FakeSession()

    client = MassiveHttpClient(
        api_key="test-api-key",
        session=session,
    )

    bars = client.get_aggregate_bars(
        ticker="O:SPY270319C00685000",
        start_date="2026-01-08",
        end_date="2026-01-08",
    )

    assert session.calls == 2
    assert len(bars) == 1
    assert bars[0]["c"] == 11

@pytest.mark.integration
def test_massive_daily_leaps_one_month_backtest_smoke():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # =====================================================
    # Real SPY history
    #
    # yfinance end date is effectively exclusive,
    # so use 2026-01-31 to include Jan 30.
    # =====================================================

    spy_data = download_price_data(
        ticker="SPY",
        start_date="2026-01-02",
        end_date="2026-01-31",
    )

    assert not spy_data.empty

    prices = pd.Series(
        data=spy_data["close"].astype(float).to_numpy(),
        index=pd.to_datetime(
            spy_data["date"]
        ),
        dtype=float,
    )

    assert len(prices) > 5
    assert not prices.isna().any()

    print(
        "\nSPY historical window:",
        prices.index[0],
        "->",
        prices.index[-1],
    )

    print(
        "Trading days:",
        len(prices),
    )

    # =====================================================
    # Massive infrastructure
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
    )

    option_bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    # =====================================================
    # Pre-resolve Day-1 contract and preload its
    # complete one-month daily-bar range.
    # =====================================================

    option_bar_provider.set_backtest_range(
        start_date=prices.index[0],
        end_date=prices.index[-1],
    )

    # =====================================================
    # Strategy
    # =====================================================

    initial_capital = 100000.0

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=initial_capital,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=1,
        take_profit_threshold=0.25,
    )

    portfolio = Portfolio(
        initial_cash=initial_capital,
    )

    engine = BacktestEngine()

    # =====================================================
    # Run one-month real historical backtest
    # =====================================================

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_bar_provider=option_bar_provider,
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    # =====================================================
    # Lifecycle invariants
    # =====================================================

    assert len(
        result.equity_curve
    ) == len(prices)

    assert len(strategy.tranches) == 1

    tranche = strategy.tranches[0]

    # assert tranche.option_contract == (
    #     preload_contract
    # )

    assert tranche.equity_deployed is True
    assert tranche.option_deployed is True
    assert tranche.option_contract is not None

    contract = tranche.option_contract

    assert contract.underlying == "SPY"

    print(
        "\nResolved contract:",
        contract,
    )

    print(
        "Massive ticker:",
        format_massive_option_ticker(
            contract
        ),
    )

    # =====================================================
    # NAV integrity
    # =====================================================

    assert all(
        nav > 0
        for nav in result.equity_curve
    )

    assert not any(
        pd.isna(nav)
        for nav in result.equity_curve
    )

    assert portfolio.cash >= 0

    # =====================================================
    # Option lifecycle
    #
    # Real historical data decides whether TP fires.
    # =====================================================

    contract = tranche.option_contract

    if contract in portfolio.option_positions:

        option_position = (
            portfolio.option_positions[
                contract
            ]
        )

        assert option_position.quantity > 0
        assert option_position.average_cost > 0

        print(
            "Option status: OPEN"
        )

        print(
            "Option quantity:",
            option_position.quantity,
        )

        print(
            "Option average cost:",
            option_position.average_cost,
        )

    else:

        assert tranche.option_closed is True

        print(
            "Option status: CLOSED"
        )

    # =====================================================
    # Summary
    # =====================================================

    initial_nav = (
        result.equity_curve[0]
    )

    ending_nav = (
        result.equity_curve[-1]
    )

    total_return = (
        ending_nav
        / initial_nav
        - 1.0
    )

    print(
        "Initial NAV:",
        initial_nav,
    )

    print(
        "Ending NAV:",
        ending_nav,
    )

    print(
        "Return:",
        total_return,
    )

    print(
        "Minimum NAV:",
        min(
            result.equity_curve
        ),
    )

    print(
        "Maximum NAV:",
        max(
            result.equity_curve
        ),
    )

    print(
        "Ending cash:",
        portfolio.cash,
    )


@pytest.mark.integration
def test_massive_daily_leaps_two_tranche_drawdown_backtest():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # =====================================================
    # Real SPY history around the first >= 5% drawdown
    #
    # Peak:
    # 2025-02-19 ~ 612.93
    #
    # First >= 5% drawdown:
    # 2025-03-04 ~ 576.86
    # =====================================================

    spy_data = download_price_data(
        ticker="SPY",
        start_date="2025-02-18",
        end_date="2025-03-08",
    )

    assert not spy_data.empty

    prices = pd.Series(
        data=spy_data["close"].astype(float).to_numpy(),
        index=pd.to_datetime(
            spy_data["date"]
        ),
        dtype=float,
    )

    assert len(prices) > 5
    assert not prices.isna().any()

    print(
        "\nSPY window:",
        prices.index[0],
        "->",
        prices.index[-1],
    )

    # =====================================================
    # Massive infrastructure
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
    )

    option_bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    option_bar_provider.set_backtest_range(
        start_date=prices.index[0],
        end_date=prices.index[-1],
    )

    # =====================================================
    # Strategy
    # =====================================================

    initial_capital = 100000.0

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=initial_capital,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=2,
        take_profit_threshold=0.25,
    )

    portfolio = Portfolio(
        initial_cash=initial_capital,
    )

    engine = BacktestEngine()

    # =====================================================
    # Run
    # =====================================================

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_bar_provider=option_bar_provider,
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    # =====================================================
    # Core two-tranche lifecycle assertions
    # =====================================================

    assert len(
        result.equity_curve
    ) == len(prices)

    assert len(strategy.tranches) >= 2

    first = strategy.tranches[0]
    second = strategy.tranches[1]

    assert first.equity_deployed is True
    assert first.option_deployed is True

    assert second.equity_deployed is True
    assert second.option_deployed is True

    assert first.option_contract is not None
    assert second.option_contract is not None

    # =====================================================
    # Portfolio integrity
    # =====================================================

    assert portfolio.position.quantity > 0

    assert portfolio.cash >= 0

    assert all(
        nav > 0
        for nav in result.equity_curve
    )

    assert not any(
        pd.isna(nav)
        for nav in result.equity_curve
    )

    # =====================================================
    # Diagnostics
    # =====================================================

    print(
        "Tranche count:",
        len(strategy.tranches),
    )

    for i, tranche in enumerate(
        strategy.tranches,
        start=1,
    ):
        print(
            f"Tranche {i}:",
            tranche.option_contract,
            "equity_deployed=",
            tranche.equity_deployed,
            "option_deployed=",
            tranche.option_deployed,
            "option_closed=",
            tranche.option_closed,
        )

    print(
        "Current option positions:"
    )

    for (
        contract,
        position,
    ) in portfolio.option_positions.items():
        print(
            contract,
            "quantity=",
            position.quantity,
            "average_cost=",
            position.average_cost,
        )

    initial_nav = (
        result.equity_curve[0]
    )

    ending_nav = (
        result.equity_curve[-1]
    )

    total_return = (
        ending_nav
        / initial_nav
        - 1.0
    )

    print(
        "Initial NAV:",
        initial_nav,
    )

    print(
        "Ending NAV:",
        ending_nav,
    )

    print(
        "Return:",
        total_return,
    )

    print(
        "Minimum NAV:",
        min(
            result.equity_curve
        ),
    )

    print(
        "Maximum NAV:",
        max(
            result.equity_curve
        ),
    )

    print(
        "Ending cash:",
        portfolio.cash,
    )

    final_spy_price = float(
        prices.iloc[-1]
    )

    equity_value = (
        portfolio.position.quantity
        * final_spy_price
    )

    option_value = 0.0

    for (
        contract,
        position,
    ) in portfolio.option_positions.items():

        bar = option_bar_provider.get_bar(
            timestamp=prices.index[-1],
            contract=contract,
        )

        pricing = (
            DailyCloseOptionPricingPolicy()
            .get_pricing(
                bar=bar,
            )
        )

        option_value += (
            position.quantity
            * pricing.mark_price
            * contract.multiplier
        )

    expected_nav = (
        portfolio.cash
        + equity_value
        + option_value
    )

    assert result.equity_curve[-1] == pytest.approx(
        expected_nav
    )

    print(
        "Final SPY value:",
        equity_value,
    )

    print(
        "Final option value:",
        option_value,
    )

    print(
        "Reconciled NAV:",
        expected_nav,
    )

@pytest.mark.integration
def test_massive_real_leaps_take_profit_window_discovery():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # =====================================================
    # Choose a historical start date.
    #
    # We use a relatively long forward window so that
    # the selected LEAPS has a realistic chance of
    # gaining >= 25%.
    # =====================================================

    start_date = pd.Timestamp(
        "2025-04-01"
    )

    end_date = pd.Timestamp(
        "2025-12-31"
    )

    # =====================================================
    # Real SPY price on the start date
    # =====================================================

    spy_data = download_price_data(
        ticker="SPY",
        start_date=start_date.strftime(
            "%Y-%m-%d"
        ),
        end_date=(
            start_date
            + pd.Timedelta(days=7)
        ).strftime("%Y-%m-%d"),
    )

    assert not spy_data.empty

    prices = pd.Series(
        data=spy_data[
            "close"
        ].astype(float).to_numpy(),
        index=pd.to_datetime(
            spy_data["date"]
        ),
        dtype=float,
    )

    entry_date = prices.index[0]

    underlying_price = float(
        prices.iloc[0]
    )

    print(
        "\nEntry date:",
        entry_date,
    )

    print(
        "SPY entry price:",
        underlying_price,
    )

    # =====================================================
    # Massive infrastructure
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
    )

    option_bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    # =====================================================
    # Dynamically select the entry LEAPS
    # =====================================================

    contract = resolver.resolve(
        timestamp=entry_date,
        underlying_price=underlying_price,
    )

    print(
        "Resolved contract:",
        contract,
    )

    print(
        "Massive ticker:",
        format_massive_option_ticker(
            contract
        ),
    )

    # =====================================================
    # Fetch the entire forward option history in one call
    # =====================================================

    bars = option_bar_provider.get_bars(
        contract=contract,
        start_date=entry_date,
        end_date=end_date,
    )

    assert bars

    # =====================================================
    # Find the actual entry bar
    # =====================================================

    bars_by_date = {
        pd.Timestamp(
            bar.timestamp
        ).normalize(): bar
        for bar in bars
    }

    entry_key = pd.Timestamp(
        entry_date
    ).normalize()

    assert entry_key in bars_by_date

    entry_bar = bars_by_date[
        entry_key
    ]

    entry_price = float(
        entry_bar.close
    )

    assert entry_price > 0

    print(
        "Option entry close:",
        entry_price,
    )

    # =====================================================
    # Find first >= 25% close-to-close gain
    # =====================================================

    take_profit_threshold = 0.25

    tp_bar = None
    tp_return = None

    for bar in bars:

        bar_date = pd.Timestamp(
            bar.timestamp
        ).normalize()

        if bar_date <= entry_key:
            continue

        option_return = (
            float(bar.close)
            / entry_price
            - 1.0
        )

        if (
            option_return
            >= take_profit_threshold
        ):
            tp_bar = bar
            tp_return = option_return
            break

    assert tp_bar is not None, (
        "No >= 25% LEAPS take-profit "
        "event found in the selected window"
    )

    tp_date = pd.Timestamp(
        tp_bar.timestamp
    ).normalize()

    print(
        "First TP date:",
        tp_date,
    )

    print(
        "TP close:",
        tp_bar.close,
    )

    print(
        "Option return:",
        tp_return,
    )

    assert tp_return >= 0.25

@pytest.mark.integration
def test_massive_real_leaps_take_profit_and_recycling_backtest():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # =====================================================
    # Real SPY window covering the known LEAPS TP event
    # =====================================================

    spy_data = download_price_data(
        ticker="SPY",
        start_date="2025-04-01",
        end_date="2025-05-17",
    )

    assert not spy_data.empty

    prices = pd.Series(
        data=spy_data["close"].astype(float).to_numpy(),
        index=pd.to_datetime(
            spy_data["date"]
        ),
        dtype=float,
    )

    assert not prices.empty
    assert not prices.isna().any()

    # =====================================================
    # Massive infrastructure
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
    )

    option_bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    option_bar_provider.set_backtest_range(
        start_date=prices.index[0],
        end_date=prices.index[-1],
    )

    # =====================================================
    # Strategy
    #
    # max_tranches=1 is intentional.
    #
    # We are testing option-capacity recycling rather
    # than equity drawdown ladder deployment.
    # =====================================================

    initial_capital = 100000.0

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=initial_capital,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=1,
        take_profit_threshold=0.25,
    )

    portfolio = Portfolio(
        initial_cash=initial_capital,
    )

    engine = BacktestEngine()

    # =====================================================
    # Run
    # =====================================================

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_bar_provider=option_bar_provider,
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    # =====================================================
    # General integrity
    # =====================================================

    assert len(
        result.equity_curve
    ) == len(prices)

    assert all(
        nav > 0
        for nav in result.equity_curve
    )

    assert not any(
        pd.isna(nav)
        for nav in result.equity_curve
    )

    # =====================================================
    # Recycling lifecycle
    # =====================================================

    assert len(strategy.tranches) == 1

    first = strategy.tranches[0]

    assert first.equity_deployed is True
    assert first.option_deployed is False
    assert first.option_closed is True

    assert first.option_contract is not None

    assert strategy.active_equity_tranches == 1
    assert strategy.active_option_tranches == 0

    assert first.option_contract not in portfolio.option_positions

    assert portfolio.realized_pnl > 0

    print(
        "\nTranche count:",
        len(strategy.tranches),
    )

    print(
        "First contract:",
        first.option_contract,
    )

    print(
        "equity_deployed:",
        first.equity_deployed,
    )

    print(
        "option_deployed:",
        first.option_deployed,
    )

    print(
        "option_closed:",
        first.option_closed,
    )

    print(
        "Active equity tranches:",
        strategy.active_equity_tranches,
    )

    print(
        "Active option tranches:",
        strategy.active_option_tranches,
    )

    print(
        "Realized PnL:",
        portfolio.realized_pnl,
    )

    print(
        "Ending cash:",
        portfolio.cash,
    )

    print(
        "Ending NAV:",
        result.equity_curve[-1],
    )

@pytest.mark.integration
def test_massive_real_leaps_tp_then_drawdown_redeploys_option():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # =====================================================
    # Real SPY window:
    #
    # 2025-04-01:
    # initial LEAPS entry
    #
    # 2025-05-13:
    # known >= 25% option TP
    #
    # 2025-11-20:
    # known >= 5% post-TP SPY drawdown
    # =====================================================

    spy_data = download_price_data(
        ticker="SPY",
        start_date="2025-04-01",
        end_date="2025-11-22",
    )

    assert not spy_data.empty

    prices = pd.Series(
        data=spy_data["close"].astype(float).to_numpy(),
        index=pd.to_datetime(
            spy_data["date"]
        ),
        dtype=float,
    )

    assert not prices.empty
    assert not prices.isna().any()

    # =====================================================
    # Massive infrastructure
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
    )

    option_bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    option_bar_provider.set_backtest_range(
        start_date=prices.index[0],
        end_date=prices.index[-1],
    )

    # =====================================================
    # Strategy
    #
    # max_tranches=2 allows:
    #
    # tranche 1:
    # initial equity + option
    #
    # tranche 2:
    # later drawdown deployment after option capacity
    # has been released by TP.
    # =====================================================

    initial_capital = 100000.0

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=initial_capital,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=2,
        take_profit_threshold=0.25,
    )

    portfolio = Portfolio(
        initial_cash=initial_capital,
    )

    engine = BacktestEngine()

    # =====================================================
    # Run
    # =====================================================

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_bar_provider=option_bar_provider,
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    # =====================================================
    # General integrity
    # =====================================================

    assert len(
        result.equity_curve
    ) == len(prices)

    assert all(
        nav > 0
        for nav in result.equity_curve
    )

    assert not any(
        pd.isna(nav)
        for nav in result.equity_curve
    )

    # =====================================================
    # Lifecycle
    # =====================================================

    assert len(strategy.tranches) >= 2

    first = strategy.tranches[0]

    assert first.equity_deployed is True
    assert first.option_closed is True
    assert first.option_deployed is False

    later_option_tranches = [
        tranche
        for tranche in strategy.tranches[1:]
        if tranche.option_deployed
    ]

    assert later_option_tranches

    redeployed = (
        later_option_tranches[0]
    )

    assert (
        redeployed.option_contract
        is not None
    )

    # =====================================================
    # Capacity state
    # =====================================================

    assert (
        strategy.active_equity_tranches
        <= strategy.max_tranches
    )

    assert (
        strategy.active_option_tranches
        <= strategy.max_tranches
    )

    # =====================================================
    # Diagnostics
    # =====================================================

    print(
        "\nTrading days:",
        len(prices),
    )

    print(
        "Tranche count:",
        len(strategy.tranches),
    )

    for i, tranche in enumerate(
        strategy.tranches,
        start=1,
    ):
        print(
            f"Tranche {i}:",
            tranche.option_contract,
            "level=",
            tranche.level,
            "equity_deployed=",
            tranche.equity_deployed,
            "option_deployed=",
            tranche.option_deployed,
            "option_closed=",
            tranche.option_closed,
        )

    print(
        "First TP contract:",
        first.option_contract,
    )

    print(
        "Redeployed contract:",
        redeployed.option_contract,
    )

    print(
        "Active equity tranches:",
        strategy.active_equity_tranches,
    )

    print(
        "Active option tranches:",
        strategy.active_option_tranches,
    )

    print(
        "Current option positions:"
    )

    for (
        contract,
        position,
    ) in portfolio.option_positions.items():

        print(
            contract,
            "quantity=",
            position.quantity,
            "average_cost=",
            position.average_cost,
        )

    initial_nav = (
        result.equity_curve[0]
    )

    ending_nav = (
        result.equity_curve[-1]
    )

    print(
        "Initial NAV:",
        initial_nav,
    )

    print(
        "Ending NAV:",
        ending_nav,
    )

    print(
        "Return:",
        ending_nav
        / initial_nav
        - 1.0,
    )

    print(
        "Minimum NAV:",
        min(
            result.equity_curve
        ),
    )

    print(
        "Maximum NAV:",
        max(
            result.equity_curve
        ),
    )

    print(
        "Ending cash:",
        portfolio.cash,
    )

    print(
        "Realized PnL:",
        portfolio.realized_pnl,
    )

    assert strategy.active_equity_tranches == 2
    assert strategy.active_option_tranches == 1

    assert len(strategy.tranches) == 3

    recycled = strategy.tranches[-1]

    assert recycled.equity_deployed is False
    assert recycled.option_deployed is True
    assert recycled.option_closed is False
    assert recycled.option_contract is not None

    assert (
        strategy.active_equity_tranches
        == sum(
            tranche.equity_deployed
            for tranche in strategy.tranches
        )
    )

    assert (
        strategy.active_option_tranches
        == sum(
            tranche.option_deployed
            and not tranche.option_closed
            for tranche in strategy.tranches
        )
    )

@pytest.mark.integration
def test_massive_daily_leaps_one_year_backtest_smoke():
    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    # =====================================================
    # Real SPY history: full calendar year 2025
    # =====================================================

    spy_data = download_price_data(
        ticker="SPY",
        start_date="2025-01-02",
        end_date="2026-01-01",
    )

    assert not spy_data.empty

    prices = pd.Series(
        data=spy_data["close"].astype(float).to_numpy(),
        index=pd.to_datetime(
            spy_data["date"]
        ),
        dtype=float,
    )

    assert len(prices) > 200
    assert not prices.isna().any()

    # =====================================================
    # Massive infrastructure
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    option_bar_provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    option_bar_provider.set_backtest_range(
        start_date=prices.index[0],
        end_date=prices.index[-1],
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
        min_days_to_expiration=365,
        max_days_to_expiration=548,
        target_days_to_expiration=456,
        tradability_provider=(
            option_bar_provider
        ),
    )

    option_bar_provider.set_backtest_range(
        start_date=prices.index[0],
        end_date=prices.index[-1],
    )

    # =====================================================
    # Strategy
    # =====================================================

    initial_capital = 100000.0

    strategy = SpyLeapsLadderStrategy(
        contract_resolver=resolver,
        initial_capital=initial_capital,
        equity_allocation=0.25,
        option_allocation=0.25,
        max_tranches=2,
        take_profit_threshold=0.25,
    )

    portfolio = Portfolio(
        initial_cash=initial_capital,
    )

    engine = BacktestEngine()

    # =====================================================
    # Run
    # =====================================================

    result = engine.run(
        prices=prices,
        strategy=strategy,
        portfolio=portfolio,
        option_bar_provider=option_bar_provider,
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    # =====================================================
    # NAV integrity
    # =====================================================

    assert len(
        result.equity_curve
    ) == len(prices)

    assert all(
        nav > 0
        for nav in result.equity_curve
    )

    assert not any(
        pd.isna(nav)
        for nav in result.equity_curve
    )

    assert portfolio.cash >= 0

    # =====================================================
    # Capacity / ledger invariants
    # =====================================================

    assert (
        strategy.active_equity_tranches
        == sum(
            tranche.equity_deployed
            for tranche in strategy.tranches
        )
    )

    assert (
        strategy.active_option_tranches
        == sum(
            tranche.option_deployed
            and not tranche.option_closed
            for tranche in strategy.tranches
        )
    )

    assert (
        strategy.active_equity_tranches
        <= strategy.max_tranches
    )

    assert (
        strategy.active_option_tranches
        <= strategy.max_tranches
    )

    # =====================================================
    # Build NAV series
    # =====================================================

    nav = pd.Series(
        result.equity_curve,
        index=prices.index,
        dtype=float,
    )

    initial_nav = float(
        nav.iloc[0]
    )

    ending_nav = float(
        nav.iloc[-1]
    )

    total_return = (
        ending_nav
        / initial_nav
        - 1.0
    )

    running_peak = nav.cummax()

    drawdown = (
        nav
        / running_peak
        - 1.0
    )

    max_drawdown = float(
        drawdown.min()
    )

    # Drawdown convention:
    # 0 at highs, negative below highs.
    assert max_drawdown <= 0.0
    assert max_drawdown > -1.0

    # =====================================================
    # Diagnostics
    # =====================================================

    print(
        "\nTrading days:",
        len(prices),
    )

    print(
        "Lifecycle tranche count:",
        len(strategy.tranches),
    )

    print(
        "Active equity tranches:",
        strategy.active_equity_tranches,
    )

    print(
        "Active option tranches:",
        strategy.active_option_tranches,
    )

    print(
        "\nLifecycle ledger:"
    )

    for i, tranche in enumerate(
        strategy.tranches,
        start=1,
    ):
        print(
            f"Tranche {i}:",
            "level=",
            tranche.level,
            "contract=",
            tranche.option_contract,
            "equity_deployed=",
            tranche.equity_deployed,
            "option_deployed=",
            tranche.option_deployed,
            "option_closed=",
            tranche.option_closed,
        )

    print(
        "\nCurrent option positions:"
    )

    for (
        contract,
        position,
    ) in portfolio.option_positions.items():

        print(
            contract,
            "quantity=",
            position.quantity,
            "average_cost=",
            position.average_cost,
        )

    print(
        "\nInitial NAV:",
        initial_nav,
    )

    print(
        "Ending NAV:",
        ending_nav,
    )

    print(
        "Total return:",
        total_return,
    )

    print(
        "Maximum drawdown:",
        max_drawdown,
    )

    print(
        "Minimum NAV:",
        float(nav.min()),
    )

    print(
        "Maximum NAV:",
        float(nav.max()),
    )

    print(
        "Ending cash:",
        portfolio.cash,
    )

    print(
        "Realized PnL:",
        portfolio.realized_pnl,
    )

@pytest.mark.integration
def test_massive_option_first_available_bar_diagnostic():
    api_key = os.getenv("MASSIVE_API_KEY")

    if not api_key:
        pytest.skip(
            "MASSIVE_API_KEY is not configured"
        )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp(
            "2026-03-20"
        ),
        strike=585.0,
        option_type=OptionType.CALL,
    )

    client = MassiveHttpClient(
        api_key=api_key,
    )

    provider = (
        MassiveHistoricalOptionBarProvider(
            client=client,
        )
    )

    bars = provider.get_bars(
        contract=contract,
        start_date=pd.Timestamp(
            "2025-01-02"
        ),
        end_date=pd.Timestamp(
            "2025-01-31"
        ),
    )

    print(
        "\nContract:",
        contract,
    )

    print(
        "Ticker:",
        format_massive_option_ticker(
            contract
        ),
    )

    print(
        "Bars returned:",
        len(bars),
    )

    for bar in bars[:10]:
        print(
            bar.timestamp,
            "close=",
            bar.close,
            "volume=",
            bar.volume,
        )

    if bars:
        print(
            "First available bar:",
            bars[0],
        )

