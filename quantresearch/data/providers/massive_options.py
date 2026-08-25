import pandas as pd
import requests
import time

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

from quantresearch.data.historical_option_bar import (
    HistoricalOptionBar
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

def normalize_massive_option_bar(
    raw_bar: dict,
    contract: OptionContract,
) -> HistoricalOptionBar:

    required_fields = {
        "o",
        "h",
        "l",
        "c",
        "t",
    }

    missing_fields = (
        required_fields
        - set(raw_bar)
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

    return HistoricalOptionBar(
        contract=contract,
        timestamp=pd.to_datetime(
            raw_bar["t"],
            unit="ms",
        ),
        open=float(
            raw_bar["o"]
        ),
        high=float(
            raw_bar["h"]
        ),
        low=float(
            raw_bar["l"]
        ),
        close=float(
            raw_bar["c"]
        ),
        volume=(
            float(raw_bar["v"])
            if "v" in raw_bar
            else None
        ),
        vwap=(
            float(raw_bar["vw"])
            if "vw" in raw_bar
            else None
        ),
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

    def _get_with_retry(
        self,
        url,
        params=None,
        headers=None,
        max_retries: int = 5,
        initial_wait_seconds: float = 15.0,
    ):

        wait_seconds = initial_wait_seconds

        for attempt in range(
            max_retries + 1
        ):

            response = self.session.get(
                url,
                params=params,
                headers=headers,
            )

            if response.status_code != 429:

                response.raise_for_status()

                return response

            if attempt == max_retries:

                print(
                    "Massive API rate limit: "
                    "maximum retries exhausted."
                )

                response.raise_for_status()

            retry_after = response.headers.get(
                "Retry-After"
            )

            if retry_after is not None:

                wait_seconds = float(
                    retry_after
                )

            print(
                "Massive API rate limit (429). "
                f"Retry {attempt + 1}/{max_retries} "
                f"in {wait_seconds:.0f} seconds..."
            )

            time.sleep(
                wait_seconds
            )

            wait_seconds *= 2

    def get_quotes(
        self,
        ticker: str,
        start_date,
        end_date,
    ):

        url = (
            f"{self.BASE_URL}/v3/quotes/"
            f"{ticker}"
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

        results = []

        while url:

            response = self._get_with_retry(
                url=url,
                params=params,
                headers=headers,
            )

            payload = response.json()

            results.extend(
                payload.get("results", [])
            )

            url = payload.get("next_url")

            params = None

        return results

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
        expiration_date_gte=None,
        expiration_date_lte=None,
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
            "expired": "false",
            "order": "asc",
            "sort": "expiration_date",
            "limit": 1000,
        }

        if expiration_date_gte is not None:

            params["expiration_date.gte"] = (
                pd.Timestamp(
                    expiration_date_gte
                ).strftime("%Y-%m-%d")
            )

        if expiration_date_lte is not None:

            params["expiration_date.lte"] = (
                pd.Timestamp(
                    expiration_date_lte
                ).strftime("%Y-%m-%d")
            )

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            )
        }

        contracts = []

        while url is not None:

            response = self._get_with_retry(
                url=url,
                params=params,
                headers=headers,
            )

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
        expiration_date_gte=None,
        expiration_date_lte=None,
    ):

        raw_contracts = (
            self.client.get_option_contracts(
                underlying_ticker=self.underlying,
                as_of=timestamp,
                expiration_date_gte=expiration_date_gte,
                expiration_date_lte=expiration_date_lte,
            )
        )

        return [
            normalize_massive_option_contract(
                raw_contract
            )
            for raw_contract in raw_contracts
        ]

class MassiveHistoricalOptionBarProvider:

    def __init__(
        self,
        client,
    ):
        self.client = client

    def get_bars(
        self,
        contract,
        start_date,
        end_date,
    ):

        ticker = format_massive_option_ticker(
            contract
        )

        raw_bars = (
            self.client.get_aggregate_bars(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                start_date=start_date,
                end_date=end_date,
            )
        )

        return [
            normalize_massive_option_bar(
                raw_bar=raw_bar,
                contract=contract,
            )
            for raw_bar in raw_bars
        ]

class MassiveHistoricalOptionBarProvider:

    def __init__(
        self,
        client,
    ):
        self.client = client

    def get_bars(
        self,
        contract,
        start_date,
        end_date,
    ):

        ticker = format_massive_option_ticker(
            contract
        )

        raw_bars = self.client.get_aggregate_bars(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            start_date=start_date,
            end_date=end_date,
        )

        return [
            normalize_massive_option_bar(
                raw_bar=raw_bar,
                contract=contract,
            )
            for raw_bar in raw_bars
        ]