from abc import ABC, abstractmethod

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)
from quantresearch.instruments.options import OptionContract


class HistoricalOptionDataProvider(ABC):

    @abstractmethod
    def get_quote(
        self,
        timestamp,
        contract: OptionContract,
    ) -> HistoricalOptionQuote:
        pass