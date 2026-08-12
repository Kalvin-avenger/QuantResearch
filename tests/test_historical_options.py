import pandas as pd

from quantresearch.data.historical_options import HistoricalOptionQuoteStore
from quantresearch.data.options import OptionQuote
from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def test_historical_option_quote_store_returns_quote_by_timestamp_and_contract():
    timestamp = pd.Timestamp("2026-01-02")

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=contract,
        last_trade_date=timestamp,
        last_price=25.0,
        bid=24.5,
        ask=25.5,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    store = HistoricalOptionQuoteStore(
        quotes={
            timestamp: {
                contract: quote,
            }
        }
    )

    result = store.get_quote(
        timestamp=timestamp,
        contract=contract,
    )

    assert result == quote

import pytest


def test_historical_option_quote_store_rejects_missing_timestamp():
    timestamp = pd.Timestamp("2026-01-02")

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    store = HistoricalOptionQuoteStore(
        quotes={}
    )

    with pytest.raises(
        ValueError,
        match="timestamp",
    ):
        store.get_quote(
            timestamp=timestamp,
            contract=contract,
        )

def test_historical_option_quote_store_rejects_missing_contract():
    timestamp = pd.Timestamp("2026-01-02")

    requested_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    other_contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=510.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=other_contract,
        last_trade_date=timestamp,
        last_price=20.0,
        bid=19.5,
        ask=20.5,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    store = HistoricalOptionQuoteStore(
        quotes={
            timestamp: {
                other_contract: quote,
            }
        }
    )

    with pytest.raises(
        ValueError,
        match="contract",
    ):
        store.get_quote(
            timestamp=timestamp,
            contract=requested_contract,
        )

def test_historical_option_quote_store_normalizes_timestamp_to_date():
    stored_timestamp = pd.Timestamp("2026-01-02")

    requested_timestamp = pd.Timestamp(
        "2026-01-02 15:30:00"
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = OptionQuote(
        contract=contract,
        last_trade_date=stored_timestamp,
        last_price=25.0,
        bid=24.5,
        ask=25.5,
        volume=100,
        open_interest=1000,
        implied_volatility=0.20,
        in_the_money=False,
    )

    store = HistoricalOptionQuoteStore(
        quotes={
            stored_timestamp: {
                contract: quote,
            }
        }
    )

    result = store.get_quote(
        timestamp=requested_timestamp,
        contract=contract,
    )

    assert result == quote

from quantresearch.data.option_provider import HistoricalOptionDataProvider


def test_historical_option_quote_store_is_data_provider():
    store = HistoricalOptionQuoteStore(
        quotes={}
    )

    assert isinstance(
        store,
        HistoricalOptionDataProvider,
    )

def test_historical_option_quote_store_from_dataframe():
    data = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-02",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 500.0,
                "option_type": "CALL",
                "last_price": 25.0,
                "bid": 24.5,
                "ask": 25.5,
                "volume": 100,
                "open_interest": 1000,
                "implied_volatility": 0.20,
                "in_the_money": False,
            }
        ]
    )

    store = HistoricalOptionQuoteStore.from_dataframe(
        data
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
    )

    assert quote.contract == contract
    
    assert quote.bid == pytest.approx(24.5)
    assert quote.ask == pytest.approx(25.5)

    quote = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
    )

    assert isinstance(
        quote,
        HistoricalOptionQuote,
    )

    assert quote.contract == contract
    assert quote.bid == pytest.approx(24.5)
    assert quote.ask == pytest.approx(25.5)

def test_historical_option_quote_store_from_dataframe_supports_multiple_dates_and_contracts():
    data = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-02",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 500.0,
                "option_type": "CALL",
                "last_price": 25.0,
                "bid": 24.5,
                "ask": 25.5,
                "volume": 100,
                "open_interest": 1000,
                "implied_volatility": 0.20,
                "in_the_money": False,
            },
            {
                "timestamp": "2026-01-02",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 510.0,
                "option_type": "CALL",
                "last_price": 20.0,
                "bid": 19.5,
                "ask": 20.5,
                "volume": 80,
                "open_interest": 900,
                "implied_volatility": 0.21,
                "in_the_money": False,
            },
            {
                "timestamp": "2026-01-05",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 500.0,
                "option_type": "CALL",
                "last_price": 27.0,
                "bid": 26.5,
                "ask": 27.5,
                "volume": 120,
                "open_interest": 1100,
                "implied_volatility": 0.22,
                "in_the_money": True,
            },
        ]
    )

    store = HistoricalOptionQuoteStore.from_dataframe(
        data
    )

    contract_500 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_510 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=510.0,
        option_type=OptionType.CALL,
    )

    quote_500_day_1 = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract_500,
    )

    quote_510_day_1 = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract_510,
    )

    quote_500_day_2 = store.get_quote(
        timestamp=pd.Timestamp("2026-01-05"),
        contract=contract_500,
    )

    assert quote_500_day_1.bid == pytest.approx(24.5)
    assert quote_510_day_1.bid == pytest.approx(19.5)
    assert quote_500_day_2.bid == pytest.approx(26.5)

def test_historical_option_quote_store_from_dataframe_rejects_missing_columns():
    data = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-02",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 500.0,
                "option_type": "CALL",
                "last_price": 25.0,
                "bid": 24.5,
                # "ask" intentionally missing
                "volume": 100,
                "open_interest": 1000,
                "implied_volatility": 0.20,
                "in_the_money": False,
            }
        ]
    )

    with pytest.raises(
        ValueError,
        match="missing required columns",
    ):
        HistoricalOptionQuoteStore.from_dataframe(
            data
        )

def test_historical_option_quote_store_from_dataframe_rejects_duplicate_contract_quote():
    data = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-02",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 500.0,
                "option_type": "CALL",
                "last_price": 25.0,
                "bid": 24.5,
                "ask": 25.5,
                "volume": 100,
                "open_interest": 1000,
                "implied_volatility": 0.20,
                "in_the_money": False,
            },
            {
                "timestamp": "2026-01-02",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 500.0,
                "option_type": "CALL",
                "last_price": 26.0,
                "bid": 25.5,
                "ask": 26.5,
                "volume": 120,
                "open_interest": 1100,
                "implied_volatility": 0.21,
                "in_the_money": False,
            },
        ]
    )

    with pytest.raises(
        ValueError,
        match="duplicate option quote",
    ):
        HistoricalOptionQuoteStore.from_dataframe(
            data
        )

def test_historical_option_quote_store_from_csv(tmp_path):
    csv_path = tmp_path / "options.csv"

    data = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-02",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 500.0,
                "option_type": "CALL",
                "last_price": 25.0,
                "bid": 24.5,
                "ask": 25.5,
                "volume": 100,
                "open_interest": 1000,
                "implied_volatility": 0.20,
                "in_the_money": False,
            }
        ]
    )

    data.to_csv(
        csv_path,
        index=False,
    )

    store = HistoricalOptionQuoteStore.from_csv(
        csv_path
    )

    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
    )

    assert quote.contract == contract
    # assert quote.last_price == pytest.approx(25.0)
    assert quote.bid == pytest.approx(24.5)
    assert quote.ask == pytest.approx(25.5)

def test_historical_option_quote_store_from_csv_propagates_validation_errors(
    tmp_path,
):
    csv_path = tmp_path / "invalid_options.csv"

    data = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-02",
                "underlying": "SPY",
                "expiration": "2027-12-17",
                "strike": 500.0,
                "option_type": "CALL",
                "last_price": 25.0,
                "bid": 24.5,
                # ask intentionally missing
                "volume": 100,
                "open_interest": 1000,
                "implied_volatility": 0.20,
                "in_the_money": False,
            }
        ]
    )

    data.to_csv(
        csv_path,
        index=False,
    )

    with pytest.raises(
        ValueError,
        match="missing required columns",
    ):
        HistoricalOptionQuoteStore.from_csv(
            csv_path
        )

from quantresearch.data.historical_option_quote import (
    HistoricalOptionQuote,
)

def test_historical_option_quote_stores_market_data():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quote = HistoricalOptionQuote(
        contract=contract,
        timestamp=pd.Timestamp("2026-01-02 15:30:00"),
        bid=24.5,
        ask=25.5,
    )

    assert quote.contract == contract
    assert quote.timestamp == pd.Timestamp(
        "2026-01-02 15:30:00"
    )
    assert quote.bid == 24.5
    assert quote.ask == 25.5


def test_historical_option_quote_store_from_historical_quotes():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-02 10:00:00"),
            bid=24.5,
            ask=25.5,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp("2026-01-05 10:00:00"),
            bid=26.5,
            ask=27.5,
        ),
    ]

    store = HistoricalOptionQuoteStore.from_historical_quotes(
        quotes
    )

    day_1_quote = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
    )

    day_2_quote = store.get_quote(
        timestamp=pd.Timestamp("2026-01-05"),
        contract=contract,
    )

    assert day_1_quote.bid == pytest.approx(24.5)
    assert day_1_quote.ask == pytest.approx(25.5)

    assert day_2_quote.bid == pytest.approx(26.5)
    assert day_2_quote.ask == pytest.approx(27.5)

def test_historical_option_quote_store_uses_latest_quote_of_day():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 10:00:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=26.0,
            ask=27.0,
        ),
    ]

    store = HistoricalOptionQuoteStore.from_historical_quotes(
        quotes
    )

    quote = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
    )

    assert quote.timestamp == pd.Timestamp(
        "2026-01-02 15:59:00"
    )
    assert quote.bid == pytest.approx(26.0)
    assert quote.ask == pytest.approx(27.0)

def test_historical_option_quote_store_uses_latest_quote_regardless_of_input_order():
    contract = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 15:59:00"
            ),
            bid=26.0,
            ask=27.0,
        ),
        HistoricalOptionQuote(
            contract=contract,
            timestamp=pd.Timestamp(
                "2026-01-02 10:00:00"
            ),
            bid=24.0,
            ask=25.0,
        ),
    ]

    store = HistoricalOptionQuoteStore.from_historical_quotes(
        quotes
    )

    quote = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract,
    )

    assert quote.timestamp == pd.Timestamp(
        "2026-01-02 15:59:00"
    )
    assert quote.bid == pytest.approx(26.0)
    assert quote.ask == pytest.approx(27.0)

def test_historical_option_quote_store_aggregates_multiple_contracts_independently():
    contract_500 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=500.0,
        option_type=OptionType.CALL,
    )

    contract_510 = OptionContract(
        underlying="SPY",
        expiration=pd.Timestamp("2027-12-17"),
        strike=510.0,
        option_type=OptionType.CALL,
    )

    quotes = [
        HistoricalOptionQuote(
            contract=contract_500,
            timestamp=pd.Timestamp("2026-01-02 10:00:00"),
            bid=24.0,
            ask=25.0,
        ),
        HistoricalOptionQuote(
            contract=contract_510,
            timestamp=pd.Timestamp("2026-01-02 11:00:00"),
            bid=19.0,
            ask=20.0,
        ),
        HistoricalOptionQuote(
            contract=contract_500,
            timestamp=pd.Timestamp("2026-01-02 15:59:00"),
            bid=26.0,
            ask=27.0,
        ),
        HistoricalOptionQuote(
            contract=contract_510,
            timestamp=pd.Timestamp("2026-01-02 15:58:00"),
            bid=21.0,
            ask=22.0,
        ),
    ]

    store = HistoricalOptionQuoteStore.from_historical_quotes(
        quotes
    )

    quote_500 = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract_500,
    )

    quote_510 = store.get_quote(
        timestamp=pd.Timestamp("2026-01-02"),
        contract=contract_510,
    )

    assert quote_500.timestamp == pd.Timestamp(
        "2026-01-02 15:59:00"
    )
    assert quote_500.bid == pytest.approx(26.0)
    assert quote_500.ask == pytest.approx(27.0)

    assert quote_510.timestamp == pd.Timestamp(
        "2026-01-02 15:58:00"
    )
    assert quote_510.bid == pytest.approx(21.0)
    assert quote_510.ask == pytest.approx(22.0)