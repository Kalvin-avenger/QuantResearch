import pandas as pd

from quantresearch.backtest.engine import BacktestEngine
from quantresearch.data.daily_option_pricing import (
    DailyOptionExecutionQuoteAdapter,
    DailyOptionPricing,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.portfolio import Portfolio


from quantresearch.data.daily_option_pricing import (
    DailyCloseOptionPricingPolicy,
)
from quantresearch.data.historical_option_bar import (
    HistoricalOptionBar,
)


class FakeOptionDataProvider:

    def __init__(self, quote):
        self.quote = quote

    def get_quote(
        self,
        timestamp,
        contract,
    ):
        return self.quote


def test_get_option_mark_prices_prefers_explicit_mark_price():

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    pricing = DailyOptionPricing(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        buy_price=30.0,
        sell_price=29.5,
        mark_price=29.75,
    )

    quote = DailyOptionExecutionQuoteAdapter(
        pricing=pricing,
    )

    provider = FakeOptionDataProvider(
        quote=quote,
    )

    portfolio = Portfolio(
        initial_cash=100000,
    )

    # Use the same option-position construction pattern
    # already used in your existing portfolio tests.

class FakeOptionBarProvider:

    def __init__(self, bar):
        self.bar = bar

    def get_bar(
        self,
        timestamp,
        contract,
    ):
        assert timestamp == pd.Timestamp(
            "2026-01-02"
        )
        assert contract == self.bar.contract

        return self.bar


def test_engine_resolves_daily_option_bar_to_execution_quote():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    bar = HistoricalOptionBar(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02"),
        open=28.0,
        high=31.0,
        low=27.5,
        close=30.0,
        volume=1250.0,
        vwap=29.4,
    )

    provider = FakeOptionBarProvider(
        bar=bar,
    )

    engine = BacktestEngine()

    quote = engine._resolve_option_market_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
        option_data_provider=None,
        option_bar_provider=provider,
        option_pricing_policy=(
            DailyCloseOptionPricingPolicy()
        ),
    )

    assert quote.contract == contract
    assert quote.ask == 30.0
    assert quote.bid == 30.0
    assert quote.mark_price == 30.0

class FakeQuoteProvider:

    def __init__(self, quote):
        self.quote = quote

    def get_quote(
        self,
        timestamp,
        contract,
    ):
        return self.quote


def test_engine_option_market_resolver_preserves_quote_provider():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-03-19"),
        strike=505.0,
        option_type=OptionType.CALL,
    )

    class FakeQuote:
        def __init__(self):
            self.contract = contract
            self.bid = 29.0
            self.ask = 30.0

    expected_quote = FakeQuote()

    engine = BacktestEngine()

    quote = engine._resolve_option_market_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
        option_data_provider=FakeQuoteProvider(
            expected_quote
        ),
        option_bar_provider=None,
        option_pricing_policy=None,
    )

    assert quote is expected_quote