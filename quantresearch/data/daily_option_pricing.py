from dataclasses import dataclass

import pandas as pd

from quantresearch.data.historical_option_bar import HistoricalOptionBar
from quantresearch.instruments.options import OptionContract


@dataclass(frozen=True)
class DailyOptionPricing:
    """
    Explicit daily-level option pricing proxy.

    These prices are research/backtest assumptions derived from
    HistoricalOptionBar data. They are NOT historical bid/ask quotes.
    """

    contract: OptionContract
    timestamp: pd.Timestamp
    buy_price: float
    sell_price: float
    mark_price: float


class DailyCloseOptionPricingPolicy:
    """
    Daily option pricing policy using the bar close.

    BUY execution proxy  = close
    SELL execution proxy = close
    mark-to-market       = close
    """

    def get_pricing(
        self,
        bar: HistoricalOptionBar,
    ) -> DailyOptionPricing:
        close = float(bar.close)

        return DailyOptionPricing(
            contract=bar.contract,
            timestamp=bar.timestamp,
            buy_price=close,
            sell_price=close,
            mark_price=close,
        )

class DailyOptionExecutionQuoteAdapter:
    """
    Thin compatibility adapter between daily option pricing
    and the existing quote-based execution interface.

    The bid/ask attributes exposed here are execution proxies,
    not historical market quotes.
    """

    def __init__(
        self,
        pricing: DailyOptionPricing,
    ):
        self.pricing = pricing

    @property
    def contract(self) -> OptionContract:
        return self.pricing.contract

    @property
    def timestamp(self) -> pd.Timestamp:
        return self.pricing.timestamp

    @property
    def ask(self) -> float:
        return self.pricing.buy_price

    @property
    def bid(self) -> float:
        return self.pricing.sell_price

    @property
    def mark_price(self) -> float:
        return self.pricing.mark_price