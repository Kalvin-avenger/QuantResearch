import pandas as pd


from quantresearch.data.providers.massive_options import (
    MassiveOptionContractUniverseProvider,
    MassiveHttpClient,
    normalize_massive_option_contract,
    OptionType,

)



def test_massive_http_client_get_option_contracts():

    class FakeResponse:

        ok = True

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

        ok = True

        def __init__(
            self,
            payload,
        ):
            self.payload = payload

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