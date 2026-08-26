import pandas as pd

from quantresearch.data.daily_option_pricing import (
    DailyOptionPricing,
    DailyOptionExecutionQuoteAdapter,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def test_daily_option_execution_quote_adapter_maps_pricing():

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

    assert quote.contract == contract

    # Compatibility mapping for the existing
    # execution interface only.
    assert quote.ask == 30.0
    assert quote.bid == 29.5
    assert quote.mark_price == 29.75