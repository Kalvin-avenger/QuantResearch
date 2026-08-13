import pandas as pd

from quantresearch.data.providers.massive_options import (
    normalize_massive_option_quote,
)
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)
import pytest

from quantresearch.data.providers.massive_options import (
    format_massive_option_ticker,
)

from quantresearch.data.historical_options import (
    HistoricalOptionQuoteStore,
)
from quantresearch.data.providers.massive_options import (
    MassiveHttpClient,
)


def test_normalize_massive_option_quote():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    raw_quote = {
        "bid_price": 24.5,
        "ask_price": 25.5,
        "sip_timestamp": 1767398400000000000,
    }

    quote = normalize_massive_option_quote(
        raw_quote=raw_quote,
        contract=contract,
    )

    assert quote.contract == contract
    assert quote.bid == 24.5
    assert quote.ask == 25.5
    assert quote.timestamp == pd.to_datetime(
        1767398400000000000,
        unit="ns",
    )

def test_historical_option_quote_rejects_negative_bid():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    with pytest.raises(
        ValueError,
        match="bid",
    ):
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-02"),
            bid=-1.0,
            ask=25.5,
        )

def test_historical_option_quote_rejects_negative_ask():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    with pytest.raises(
        ValueError,
        match="ask",
    ):
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-02"),
            bid=24.5,
            ask=-1.0,
        )

import pytest


@pytest.mark.parametrize(
    "missing_field",
    [
        "bid_price",
        "ask_price",
        "sip_timestamp",
    ],
)
def test_normalize_massive_option_quote_rejects_missing_required_field(
    missing_field,
):
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    raw_quote = {
        "bid_price": 24.5,
        "ask_price": 25.5,
        "sip_timestamp": 1767398400000000000,
    }

    del raw_quote[missing_field]

    with pytest.raises(
        ValueError,
        match="missing required field",
    ):
        normalize_massive_option_quote(
            raw_quote=raw_quote,
            contract=contract,
        )

def test_format_massive_option_ticker():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    ticker = format_massive_option_ticker(
        contract
    )

    assert ticker == "O:SPY271217C00500000"

def test_format_massive_option_ticker_for_put():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=450.0,
        option_type=OptionType.PUT,
    )

    ticker = format_massive_option_ticker(
        contract
    )

    assert ticker == "O:SPY271217P00450000"

from quantresearch.data.providers.massive_options import (
    MassiveHistoricalOptionDataProvider,
)

def test_massive_option_provider_requests_quotes_for_contract():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    class FakeClient:
        def __init__(self):
            self.calls = []

        def get_quotes(
            self,
            ticker,
            start_date,
            end_date,
        ):
            self.calls.append(
                {
                    "ticker": ticker,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

            return [
                {
                    "bid_price": 24.5,
                    "ask_price": 25.5,
                    "sip_timestamp": 1767398400000000000,
                }
            ]

    client = FakeClient()

    provider = MassiveHistoricalOptionDataProvider(
        client=client,
    )

    quotes = provider.get_quotes(
        contract=contract,
        start_date=pd.Timestamp("2026-01-02"),
        end_date=pd.Timestamp("2026-01-02"),
    )

    assert len(client.calls) == 1

    assert client.calls[0]["ticker"] == (
        "O:SPY271217C00500000"
    )

    assert len(quotes) == 1
    assert quotes[0].contract == contract
    assert quotes[0].bid == pytest.approx(24.5)
    assert quotes[0].ask == pytest.approx(25.5)

def test_massive_option_provider_builds_quote_store():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    class FakeClient:
        def get_quotes(
            self,
            ticker,
            start_date,
            end_date,
        ):
            return [
                {
                    "bid_price": 24.5,
                    "ask_price": 25.5,
                    "sip_timestamp": pd.Timestamp(
                        "2026-01-02"
                    ).value,
                },
                {
                    "bid_price": 26.5,
                    "ask_price": 27.5,
                    "sip_timestamp": pd.Timestamp(
                        "2026-01-05"
                    ).value,
                },
            ]

    provider = MassiveHistoricalOptionDataProvider(
        client=FakeClient(),
    )

    store = provider.load_store(
        contract=contract,
        start_date=pd.Timestamp("2026-01-02"),
        end_date=pd.Timestamp("2026-01-05"),
    )

    quote = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
    )

    assert quote.contract == contract
    assert quote.bid == pytest.approx(24.5)
    assert quote.ask == pytest.approx(25.5)

def test_massive_http_client_requests_option_quotes():
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "results": [
                    {
                        "bid_price": 24.5,
                        "ask_price": 25.5,
                        "sip_timestamp": pd.Timestamp(
                            "2026-01-02 15:59:00"
                        ).value,
                    }
                ]
            }

    class FakeSession:
        def __init__(self):
            self.calls = []

        def get(
            self,
            url,
            params=None,
            headers=None,
        ):
            self.calls.append(
                {
                    "url": url,
                    "params": params,
                    "headers": headers,
                }
            )

            return FakeResponse()

    session = FakeSession()

    client = MassiveHttpClient(
        api_key="test-api-key",
        session=session,
    )

    quotes = client.get_quotes(
        ticker="O:SPY271217C00500000",
        start_date=pd.Timestamp("2026-01-02"),
        end_date=pd.Timestamp("2026-01-05"),
    )

    assert len(session.calls) == 1

    call = session.calls[0]

    assert call["url"] == (
        "https://api.massive.com/v3/quotes/"
        "O:SPY271217C00500000"
    )

    assert quotes[0]["bid_price"] == pytest.approx(24.5)
    assert quotes[0]["ask_price"] == pytest.approx(25.5)

def test_massive_http_client_follows_next_url():
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    class FakeSession:
        def __init__(self):
            self.calls = []

        def get(
            self,
            url,
            params=None,
            headers=None,
        ):
            self.calls.append(
                {
                    "url": url,
                    "params": params,
                    "headers": headers,
                }
            )

            if len(self.calls) == 1:
                return FakeResponse(
                    {
                        "results": [
                            {
                                "bid_price": 24.5,
                                "ask_price": 25.5,
                                "sip_timestamp": pd.Timestamp(
                                    "2026-01-02 10:00:00"
                                ).value,
                            }
                        ],
                        "next_url": (
                            "https://api.massive.com/v3/quotes/"
                            "O:SPY271217C00500000?cursor=abc123"
                        ),
                    }
                )

            return FakeResponse(
                {
                    "results": [
                        {
                            "bid_price": 26.5,
                            "ask_price": 27.5,
                            "sip_timestamp": pd.Timestamp(
                                "2026-01-02 15:59:00"
                            ).value,
                        }
                    ]
                }
            )

    session = FakeSession()

    client = MassiveHttpClient(
        api_key="test-api-key",
        session=session,
    )

    quotes = client.get_quotes(
        ticker="O:SPY271217C00500000",
        start_date=pd.Timestamp("2026-01-02"),
        end_date=pd.Timestamp("2026-01-02"),
    )

    assert len(session.calls) == 2
    assert len(quotes) == 2

    assert quotes[0]["bid_price"] == pytest.approx(24.5)
    assert quotes[1]["bid_price"] == pytest.approx(26.5)

    assert session.calls[1]["url"].endswith(
        "?cursor=abc123"
    )

