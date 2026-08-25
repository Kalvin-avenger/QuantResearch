import pandas as pd

import pytest

from quantresearch.data.providers.massive_options import (
    MassiveOptionContractUniverseProvider,
    MassiveHttpClient,
    normalize_massive_option_contract,
    OptionType,

)

import requests

from quantresearch.data.providers.massive_options import (
    MassiveHttpClient,
)




def test_massive_http_client_get_option_contracts():

    class FakeResponse:

        status_code = 200
        ok = True
        headers = {}

        def json(self):
            return {
                "results": [
                    {
                        "underlying_ticker": "SPY",
                        "expiration_date": "2027-04-16",
                        "strike_price": 500.0,
                        "contract_type": "call",
                    }
                ]
            }

        def raise_for_status(
            self,
        ):
            return None

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

    results = client.get_option_contracts(
        underlying_ticker="SPY",
        as_of=pd.Timestamp("2026-01-02"),
    )

    assert len(results) == 1

    assert (
        results[0]["underlying_ticker"]
        == "SPY"
    )

    call = session.calls[0]

    assert call["url"] == (
        "https://api.massive.com"
        "/v3/reference/options/contracts"
    )

    assert (
        call["params"]["underlying_ticker"]
        == "SPY"
    )

    assert (
        call["params"]["as_of"]
        == "2026-01-02"
    )

    assert (
        call["params"]["contract_type"]
        == "call"
    )

def test_massive_http_client_get_option_contracts_paginates():

    class FakeResponse:

        status_code = 200
        ok = True
        headers = {}

        def __init__(
            self,
            payload,
        ):
            self.payload = payload

        def json(
            self,
        ):
            return self.payload

        def raise_for_status(
            self,
        ):
            return None

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
                }
            )

            if len(self.calls) == 1:
                return FakeResponse(
                    {
                        "results": [
                            {"strike_price": 500.0}
                        ],
                        "next_url": (
                            "https://api.massive.com"
                            "/next-page"
                        ),
                    }
                )

            return FakeResponse(
                {
                    "results": [
                        {"strike_price": 510.0}
                    ]
                }
            )

    session = FakeSession()

    client = MassiveHttpClient(
        api_key="test-api-key",
        session=session,
    )

    results = client.get_option_contracts(
        underlying_ticker="SPY",
        as_of="2026-01-02",
    )

    assert len(results) == 2
    assert len(session.calls) == 2

    assert (
        session.calls[1]["params"]
        is None
    )

def test_normalize_massive_option_contract():

    raw = {
        "underlying_ticker": "SPY",
        "expiration_date": "2027-04-16",
        "strike_price": 500.0,
        "contract_type": "call",
    }

    contract = (
        normalize_massive_option_contract(
            raw
        )
    )

    assert contract.underlying == "SPY"

    assert (
        contract.expiration
        == pd.Timestamp(
            "2027-04-16"
        )
    )

    assert contract.strike == 500.0
    assert contract.option_type == OptionType.CALL

def test_massive_option_contract_universe_provider():

    raw_contracts = [
        {
            "underlying_ticker": "SPY",
            "expiration_date": "2027-04-16",
            "strike_price": 500.0,
            "contract_type": "call",
        },
        {
            "underlying_ticker": "SPY",
            "expiration_date": "2027-04-16",
            "strike_price": 510.0,
            "contract_type": "call",
        },
    ]

    class FakeClient:

        def __init__(self):
            self.calls = []

        def get_option_contracts(
            self,
            underlying_ticker,
            as_of,
        ):

            self.calls.append(
                (
                    underlying_ticker,
                    as_of,
                )
            )

            return raw_contracts

    client = FakeClient()

    provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    contracts = provider.get_contracts(
        timestamp=timestamp,
    )

    assert len(contracts) == 2

    assert contracts[0].strike == 500.0
    assert contracts[1].strike == 510.0

    assert client.calls == [
        (
            "SPY",
            timestamp,
        )
    ]



def test_massive_http_client_retries_after_429(monkeypatch):

    sleep_calls = []

    monkeypatch.setattr(
        "quantresearch.data.providers.massive_options.time.sleep",
        lambda seconds: sleep_calls.append(seconds),
    )

    class FakeResponse:

        def __init__(
            self,
            status_code,
            payload=None,
            headers=None,
        ):
            self.status_code = status_code
            self._payload = payload or {}
            self.headers = headers or {}

        @property
        def ok(self):
            return (
                200
                <= self.status_code
                < 400
            )

        def json(self):
            return self._payload

        def raise_for_status(self):

            if not self.ok:
                raise requests.HTTPError(
                    f"{self.status_code} error"
                )

    class FakeSession:

        def __init__(self):
            self.calls = 0

        def get(
            self,
            url,
            params=None,
            headers=None,
        ):

            self.calls += 1

            if self.calls == 1:
                return FakeResponse(
                    status_code=429,
                    headers={
                        "Retry-After": "1"
                    },
                )

            return FakeResponse(
                status_code=200,
                payload={
                    "results": []
                },
            )

    session = FakeSession()

    client = MassiveHttpClient(
        api_key="test-key",
        session=session,
    )

    response = client._get_with_retry(
        url="https://example.test",
        params={
            "test": "value"
        },
        headers={
            "Authorization": "Bearer test-key"
        },
        max_retries=2,
        initial_wait_seconds=5.0,
    )

    assert response.status_code == 200

    assert session.calls == 2

    # Retry-After takes priority over
    # the configured initial backoff.
    assert sleep_calls == [
        1.0
    ]

    def test_massive_http_client_raises_after_max_429_retries(
        monkeypatch,
    ):

        sleep_calls = []

        monkeypatch.setattr(
            "quantresearch.data.providers.massive_options.time.sleep",
            lambda seconds: sleep_calls.append(seconds),
        )

        class FakeResponse:

            status_code = 429
            headers = {}

            @property
            def ok(self):
                return False

            def raise_for_status(self):
                raise requests.HTTPError(
                    "429 Too Many Requests"
                )

        class FakeSession:

            def __init__(self):
                self.calls = 0

            def get(
                self,
                url,
                params=None,
                headers=None,
            ):
                self.calls += 1

                return FakeResponse()

        session = FakeSession()

        client = MassiveHttpClient(
            api_key="test-key",
            session=session,
        )

        with pytest.raises(
            requests.HTTPError,
            match="429",
        ):
            client._get_with_retry(
                url="https://example.test",
                max_retries=2,
                initial_wait_seconds=1.0,
            )

        # Initial request + two retries.
        assert session.calls == 3

        # Sleeps happen before retries 1 and 2.
        assert sleep_calls == [
            1.0,
            2.0,
        ]

def test_massive_http_client_filters_option_contracts_by_expiration():

    class FakeResponse:

        status_code = 200
        headers = {}

        def json(self):
            return {
                "results": [],
            }

        def raise_for_status(self):
            return None

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

    client.get_option_contracts(
        underlying_ticker="SPY",
        as_of=pd.Timestamp("2026-01-02"),
        expiration_date_gte=pd.Timestamp(
            "2027-01-02"
        ),
        expiration_date_lte=pd.Timestamp(
            "2027-07-04"
        ),
    )

    assert len(session.calls) == 1

    params = session.calls[0]["params"]

    assert (
        params["underlying_ticker"]
        == "SPY"
    )

    assert (
        params["as_of"]
        == "2026-01-02"
    )

    assert (
        params["expiration_date.gte"]
        == "2027-01-02"
    )

    assert (
        params["expiration_date.lte"]
        == "2027-07-04"
    )

    assert params["contract_type"] == "call"

def test_massive_option_contract_universe_provider_forwards_expiration_range():

    class FakeClient:

        def __init__(self):
            self.calls = []

        def get_option_contracts(
            self,
            underlying_ticker,
            as_of,
            expiration_date_gte=None,
            expiration_date_lte=None,
        ):

            self.calls.append(
                {
                    "underlying_ticker": underlying_ticker,
                    "as_of": as_of,
                    "expiration_date_gte": expiration_date_gte,
                    "expiration_date_lte": expiration_date_lte,
                }
            )

            return []

    client = FakeClient()

    provider = MassiveOptionContractUniverseProvider(
        client=client,
        underlying="SPY",
    )

    timestamp = pd.Timestamp(
        "2026-01-02"
    )

    expiration_gte = pd.Timestamp(
        "2027-01-02"
    )

    expiration_lte = pd.Timestamp(
        "2027-07-04"
    )

    provider.get_contracts(
        timestamp=timestamp,
        expiration_date_gte=expiration_gte,
        expiration_date_lte=expiration_lte,
    )

    assert client.calls == [
        {
            "underlying_ticker": "SPY",
            "as_of": timestamp,
            "expiration_date_gte": expiration_gte,
            "expiration_date_lte": expiration_lte,
        }
    ]