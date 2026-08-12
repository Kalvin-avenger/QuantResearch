import pandas as pd
from dataclasses import dataclass

from quantresearch.data.options import OptionQuote
from quantresearch.instruments.options import OptionContract
from quantresearch.data.option_provider import HistoricalOptionDataProvider
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)


class HistoricalOptionQuoteStore(
    HistoricalOptionDataProvider
):

    def __init__(
        self,
        quotes: dict,
    ):
        self.quotes = {
            self._normalize_timestamp(timestamp): quotes_at_timestamp
            for timestamp, quotes_at_timestamp in quotes.items()
        }

    @staticmethod
    def _normalize_timestamp(
        timestamp,
    ) -> pd.Timestamp:
        return pd.Timestamp(
            timestamp
        ).normalize()

    @classmethod
    def from_dataframe(
        cls,
        data: pd.DataFrame,
    ):
        required_columns = {
            "timestamp",
            "underlying",
            "expiration",
            "strike",
            "option_type",
            "bid",
            "ask",
        }

        missing_columns = (
            required_columns
            - set(data.columns)
        )

        if missing_columns:
            raise ValueError(
                "missing required columns: "
                + ", ".join(
                    sorted(missing_columns)
                )
            )
        quotes = {}

        for _, row in data.iterrows():
            timestamp = pd.Timestamp(
                row["timestamp"]
            ).normalize()

            option_type = OptionType(
                row["option_type"]
            )

            contract = OptionContract(
                underlying=row["underlying"],
                expiration=pd.Timestamp(
                    row["expiration"]
                ),
                strike=float(
                    row["strike"]
                ),
                option_type=option_type,
            )

            quote = HistoricalOptionQuote(
                contract=contract,
                timestamp=timestamp,
                bid=float(row["bid"]),
                ask=float(row["ask"]),
            )

            if timestamp not in quotes:
                quotes[timestamp] = {}

            if contract in quotes[timestamp]:
                raise ValueError(
                    "duplicate option quote for timestamp and contract"
                )

            quotes[timestamp][contract] = quote

        return cls(
            quotes=quotes
        )

    @classmethod
    def from_historical_quotes(
        cls,
        historical_quotes: list[HistoricalOptionQuote],
    ):
        quotes = {}

        for historical_quote in historical_quotes:
            timestamp = cls._normalize_timestamp(
                historical_quote.timestamp
            )

            contract = historical_quote.contract

            if timestamp not in quotes:
                quotes[timestamp] = {}

            existing_quote = quotes[timestamp].get(
                contract
            )

            if (
                existing_quote is None
                or historical_quote.timestamp
                > existing_quote.timestamp
            ):
                quotes[timestamp][contract] = historical_quote

        return cls(
            quotes=quotes
        )

    @classmethod
    def from_csv(
        cls,
        path,
    ):
        data = pd.read_csv(
            path
        )

        return cls.from_dataframe(
            data
        )

    def get_quote(
        self,
        timestamp,
        contract: OptionContract,
    ) -> OptionQuote:

        timestamp = self._normalize_timestamp(
            timestamp
        )

        if timestamp not in self.quotes:
            raise ValueError(
                "option quote timestamp not found"
            )

        quotes_at_timestamp = self.quotes[
            timestamp
        ]

        if contract not in quotes_at_timestamp:
            raise ValueError(
                "option contract quote not found"
            )

        return quotes_at_timestamp[
            contract
        ]

