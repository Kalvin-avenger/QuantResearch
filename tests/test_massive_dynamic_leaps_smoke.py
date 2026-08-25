import pandas as pd

from quantresearch.instruments.options import (
    OptionType,
)

from quantresearch.strategy.leaps_contract_resolver import (
    DynamicLeapsContractResolver,
)

from quantresearch.data.providers.massive_options import (
    MassiveOptionContractUniverseProvider,
    MassiveHistoricalOptionDataProvider,
    format_massive_option_ticker,
)


def test_massive_dynamic_leaps_historical_data_smoke():

    historical_date = pd.Timestamp(
        "2026-01-02"
    )

    spy_price = 503.0

    # =====================================================
    # Fake Massive client
    # =====================================================

    class FakeMassiveClient:

        def __init__(self):

            self.contract_calls = []
            self.quote_calls = []

        def get_option_contracts(
            self,
            underlying_ticker,
            as_of,
        ):

            self.contract_calls.append(
                (
                    underlying_ticker,
                    as_of,
                )
            )

            return [
                # Too short.
                {
                    "underlying_ticker": "SPY",
                    "expiration_date": "2026-06-19",
                    "strike_price": 500.0,
                    "contract_type": "call",
                },

                # Eligible but farther from target DTE.
                {
                    "underlying_ticker": "SPY",
                    "expiration_date": "2027-06-18",
                    "strike_price": 500.0,
                    "contract_type": "call",
                },

                # Target expiration, lower strike.
                {
                    "underlying_ticker": "SPY",
                    "expiration_date": "2027-04-16",
                    "strike_price": 490.0,
                    "contract_type": "call",
                },

                # Expected contract.
                {
                    "underlying_ticker": "SPY",
                    "expiration_date": "2027-04-16",
                    "strike_price": 500.0,
                    "contract_type": "call",
                },

                # Same expiration, farther from ATM.
                {
                    "underlying_ticker": "SPY",
                    "expiration_date": "2027-04-16",
                    "strike_price": 510.0,
                    "contract_type": "call",
                },

                # Resolver must ignore PUT.
                {
                    "underlying_ticker": "SPY",
                    "expiration_date": "2027-04-16",
                    "strike_price": 500.0,
                    "contract_type": "put",
                },
            ]

        def get_quotes(
            self,
            ticker,
            start_date,
            end_date,
        ):

            self.quote_calls.append(
                (
                    ticker,
                    start_date,
                    end_date,
                )
            )

            return [
                {
                    "bid_price": 30.0,
                    "ask_price": 31.0,
                    "sip_timestamp": (
                        pd.Timestamp(
                            "2026-01-02 15:59:00"
                        ).value
                    ),
                }
            ]

    client = FakeMassiveClient()

    # =====================================================
    # Historical contract universe
    # =====================================================

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    # =====================================================
    # Dynamic LEAPS resolver
    # =====================================================

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
    )

    selected_contract = resolver.resolve(
        timestamp=historical_date,
        underlying_price=spy_price,
    )

    # =====================================================
    # Contract-selection assertions
    # =====================================================

    assert selected_contract.underlying == "SPY"

    assert (
        selected_contract.option_type
        == OptionType.CALL
    )

    assert (
        selected_contract.expiration
        == pd.Timestamp("2027-04-16")
    )

    assert selected_contract.strike == 500.0

    assert client.contract_calls == [
        (
            "SPY",
            historical_date,
        )
    ]

    # =====================================================
    # Massive ticker normalization
    # =====================================================

    ticker = format_massive_option_ticker(
        selected_contract
    )

    assert ticker == (
        "O:SPY270416C00500000"
    )

    # =====================================================
    # Historical quote retrieval
    # =====================================================

    quote_provider = (
        MassiveHistoricalOptionDataProvider(
            client=client,
        )
    )

    quotes = quote_provider.get_quotes(
        contract=selected_contract,
        start_date=historical_date,
        end_date=historical_date,
    )

    assert len(quotes) == 1

    quote = quotes[0]

    assert quote.contract == selected_contract

    assert quote.bid == 30.0
    assert quote.ask == 31.0

    assert quote.timestamp == pd.Timestamp(
        "2026-01-02 15:59:00"
    )

    # =====================================================
    # Verify quote request used the dynamically
    # selected Massive ticker.
    # =====================================================

    assert len(client.quote_calls) == 1

    quote_call = client.quote_calls[0]

    assert quote_call[0] == (
        "O:SPY270416C00500000"
    )

    assert quote_call[1] == historical_date
    assert quote_call[2] == historical_date