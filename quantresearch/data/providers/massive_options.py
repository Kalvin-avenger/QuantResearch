import pandas as pd
import requests

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)
from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)
from quantresearch.data.historical_options import (
    HistoricalOptionQuoteStore,
)


def normalize_massive_option_quote(
    raw_quote: dict,
    contract: OptionContract,
) -> HistoricalOptionQuote:

    required_fields = {
        "bid_price",
        "ask_price",
        "sip_timestamp",
    }

    missing_fields = (
        required_fields
        - set(raw_quote)
    )

    if missing_fields:
        raise ValueError(
            "missing required field(s): "
            + ", ".join(
                sorted(missing_fields)
            )
        )

    timestamp = pd.to_datetime(
        raw_quote["sip_timestamp"],
        unit="ns",
    )

    return HistoricalOptionQuote(
        contract=contract,
        timestamp=timestamp,
        bid=float(raw_quote["bid_price"]),
        ask=float(raw_quote["ask_price"]),
    )

def format_massive_option_ticker(
    contract: OptionContract,
) -> str:

    expiration = contract.expiration.strftime(
        "%y%m%d"
    )

    option_type = (
        "C"
        if contract.option_type == OptionType.CALL
        else "P"
    )

    strike = int(
        round(
            contract.strike * 1000
        )
    )

    strike_code = f"{strike:08d}"

    return (
        f"O:{contract.underlying}"
        f"{expiration}"
        f"{option_type}"
        f"{strike_code}"
    )



class MassiveHistoricalOptionDataProvider:

    def __init__(
        self,
        client,
    ):
        self.client = client

    def get_quotes(
        self,
        contract: OptionContract,
        start_date,
        end_date,
    ) -> list[HistoricalOptionQuote]:

        ticker = format_massive_option_ticker(
            contract
        )

        raw_quotes = self.client.get_quotes(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )

        return [
            normalize_massive_option_quote(
                raw_quote=raw_quote,
                contract=contract,
            )
            for raw_quote in raw_quotes
        ]

    def load_store(
        self,
        contract: OptionContract,
        start_date,
        end_date,
    ) -> HistoricalOptionQuoteStore:

        quotes = self.get_quotes(
            contract=contract,
            start_date=start_date,
            end_date=end_date,
        )

        return HistoricalOptionQuoteStore.from_historical_quotes(
            quotes
        )


class MassiveHttpClient:

    BASE_URL = "https://api.massive.com"

    def __init__(
        self,
        api_key: str,
        session=None,
    ):
        self.api_key = api_key
        self.session = (
            session
            if session is not None
            else requests.Session()
        )

    def get_quotes(
        self,
        ticker: str,
        start_date,
        end_date,
    ) -> list[dict]:

        url = (
            f"{self.BASE_URL}"
            f"/v3/quotes/{ticker}"
        )

        params = {
            "timestamp.gte": pd.Timestamp(
                start_date
            ).strftime("%Y-%m-%d"),
            "timestamp.lte": pd.Timestamp(
                end_date
            ).strftime("%Y-%m-%d"),
            "order": "asc",
            "sort": "timestamp",
            "limit": 50000,
        }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            )
        }

        quotes = []

        while url is not None:

            response = self.session.get(
                url,
                params=params,
                headers=headers,
            )

            response.raise_for_status()
            # if not response.ok:
            #     print("status:", response.status_code)
            #     print("response:", response.text)

            # response.raise_for_status()

            data = response.json()

            quotes.extend(
                data.get(
                    "results",
                    []
                )
            )

            url = data.get(
                "next_url"
            )

            params = None

        return quotes

    def get_aggregate_bars(
        self,
        ticker: str,
        start_date,
        end_date,
        multiplier: int = 1,
        timespan: str = "day",
    ) -> list[dict]:

        url = (
            f"{self.BASE_URL}"
            f"/v2/aggs/ticker/{ticker}"
            f"/range/{multiplier}/{timespan}"
            f"/{pd.Timestamp(start_date).strftime('%Y-%m-%d')}"
            f"/{pd.Timestamp(end_date).strftime('%Y-%m-%d')}"
        )

        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
        }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            )
        }

        response = self.session.get(
            url,
            params=params,
            headers=headers,
        )

        if not response.ok:
            print("status:", response.status_code)
            print("response:", response.text)

        response.raise_for_status()

        data = response.json()

        return data.get(
            "results",
            []
        )