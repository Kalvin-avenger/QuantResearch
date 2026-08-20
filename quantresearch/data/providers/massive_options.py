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

from quantresearch.data.option_contract_universe_provider import (
    OptionContractUniverseProvider
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

def normalize_massive_option_contract(
    raw_contract: dict,
) -> OptionContract:

    required_fields = {
        "underlying_ticker",
        "expiration_date",
        "strike_price",
        "contract_type",
    }

    missing_fields = (
        required_fields
        - set(raw_contract)
    )

    if missing_fields:
        raise ValueError(
            "missing required field(s): "
            + ", ".join(
                sorted(
                    missing_fields
                )
            )
        )

    contract_type = raw_contract[
        "contract_type"
    ].lower()

    if contract_type == "call":
        option_type = OptionType.CALL

    elif contract_type == "put":
        option_type = OptionType.PUT

    else:
        raise ValueError(
            "unsupported contract_type: "
            f"{contract_type}"
        )

    return OptionContract(
        underlying=raw_contract[
            "underlying_ticker"
        ],
        expiration=pd.Timestamp(
            raw_contract[
                "expiration_date"
            ]
        ),
        strike=float(
            raw_contract[
                "strike_price"
            ]
        ),
        option_type=option_type,
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

    def get_option_contracts(
        self,
        underlying_ticker: str,
        as_of,
    ) -> list[dict]:

        url = (
            f"{self.BASE_URL}"
            f"/v3/reference/options/contracts"
        )

        params = {
            "underlying_ticker": underlying_ticker,
            "as_of": pd.Timestamp(
                as_of
            ).strftime("%Y-%m-%d"),
            "contract_type": "call",
            "expired": "true",
            "order": "asc",
            "sort": "expiration_date",
            "limit": 1000,
        }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            )
        }

        contracts = []

        while url is not None:

            response = self.session.get(
                url,
                params=params,
                headers=headers,
            )

            if not response.ok:
                response.raise_for_status()

            data = response.json()

            contracts.extend(
                data.get(
                    "results",
                    [],
                )
            )

            url = data.get(
                "next_url"
            )

            params = None

        return contracts

    
class MassiveOptionContractUniverseProvider(
    OptionContractUniverseProvider
):

    def __init__(
        self,
        client,
        underlying: str,
    ):
        self.client = client
        self.underlying = underlying

    def get_contracts(
        self,
        timestamp,
    ):

        raw_contracts = (
            self.client.get_option_contracts(
                underlying_ticker=self.underlying,
                as_of=timestamp,
            )
        )

        return [
            normalize_massive_option_contract(
                raw_contract
            )
            for raw_contract in raw_contracts
        ]