import pandas as pd

from quantresearch.data.historical_option_bar import (
    HistoricalOptionBar,
)
from quantresearch.data.daily_option_pricing import (
    DailyCloseOptionPricingPolicy,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def test_daily_close_option_pricing_uses_close_for_execution_and_mark():

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

    policy = DailyCloseOptionPricingPolicy()

    pricing = policy.get_pricing(
        bar=bar,
    )

    assert pricing.contract == contract
    assert pricing.timestamp == pd.Timestamp(
        "2026-01-02"
    )

    assert pricing.buy_price == 30.0
    assert pricing.sell_price == 30.0
    assert pricing.mark_price == 30.0