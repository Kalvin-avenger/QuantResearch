import os

import pandas as pd

from quantresearch.data.providers.massive_options import (
    MassiveHistoricalOptionDataProvider,
    MassiveHttpClient,
    MassiveOptionContractUniverseProvider,
    format_massive_option_ticker,
)
from quantresearch.strategy.leaps_contract_resolver import (
    DynamicLeapsContractResolver,
)


def main():

    api_key = os.getenv(
        "MASSIVE_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "MASSIVE_API_KEY environment variable is not set"
        )

    # =====================================================
    # Historical smoke-test configuration
    # =====================================================

    historical_date = pd.Timestamp(
        "2026-01-02"
    )

    # For this first live smoke test we supply a known
    # historical SPY reference price manually.
    #
    # Sprint 16.2 can connect historical SPY bars directly.
    spy_price = 503.0

    # =====================================================
    # Massive client
    # =====================================================

    client = MassiveHttpClient(
        api_key=api_key,
    )

    # =====================================================
    # Historical contract universe
    # =====================================================

    universe_provider = (
        MassiveOptionContractUniverseProvider(
            client=client,
            underlying="SPY",
        )
    )

    resolver = DynamicLeapsContractResolver(
        universe_provider=universe_provider,
    )

    print(
        f"Historical date: "
        f"{historical_date.date()}"
    )

    print(
        f"SPY reference price: "
        f"{spy_price:.2f}"
    )

    print(
        "Requesting historical option universe..."
    )

    selected_contract = resolver.resolve(
        timestamp=historical_date,
        underlying_price=spy_price,
    )

    # =====================================================
    # Selected contract
    # =====================================================

    ticker = format_massive_option_ticker(
        selected_contract
    )

    dte = (
        selected_contract.expiration
        - historical_date
    ).days

    print()
    print("Selected LEAPS contract")
    print("-----------------------")
    print(
        f"Underlying: "
        f"{selected_contract.underlying}"
    )
    print(
        f"Expiration: "
        f"{selected_contract.expiration.date()}"
    )
    print(
        f"DTE: "
        f"{dte}"
    )
    print(
        f"Strike: "
        f"{selected_contract.strike:.2f}"
    )
    print(
        f"Type: "
        f"{selected_contract.option_type.value}"
    )
    print(
        f"Massive ticker: "
        f"{ticker}"
    )

    # =====================================================
    # Historical quote retrieval
    # =====================================================

    quote_provider = (
        MassiveHistoricalOptionDataProvider(
            client=client,
        )
    )

    print()
    print(
        "Requesting historical option quotes..."
    )

    quotes = quote_provider.get_quotes(
        contract=selected_contract,
        start_date=historical_date,
        end_date=historical_date,
    )

    if not quotes:
        print()
        print(
            "No historical quotes were returned "
            "for the selected contract/date."
        )

        return

    # =====================================================
    # Quote diagnostics
    # =====================================================

    first_quote = quotes[0]
    last_quote = quotes[-1]

    print()
    print("Historical quote result")
    print("-----------------------")
    print(
        f"Quote count: "
        f"{len(quotes)}"
    )

    print()
    print("First quote")
    print(
        f"Timestamp: "
        f"{first_quote.timestamp}"
    )
    print(
        f"Bid: "
        f"{first_quote.bid}"
    )
    print(
        f"Ask: "
        f"{first_quote.ask}"
    )

    print()
    print("Last quote")
    print(
        f"Timestamp: "
        f"{last_quote.timestamp}"
    )
    print(
        f"Bid: "
        f"{last_quote.bid}"
    )
    print(
        f"Ask: "
        f"{last_quote.ask}"
    )

    # =====================================================
    # Basic validation
    # =====================================================

    assert (
        selected_contract.underlying
        == "SPY"
    )

    assert (
        365
        <= dte
        <= 548
    )

    assert first_quote.contract == (
        selected_contract
    )

    assert last_quote.contract == (
        selected_contract
    )

    assert first_quote.bid >= 0
    assert first_quote.ask >= 0

    assert last_quote.bid >= 0
    assert last_quote.ask >= 0

    print()
    print(
        "Massive dynamic LEAPS historical "
        "smoke test PASSED."
    )


if __name__ == "__main__":
    main()