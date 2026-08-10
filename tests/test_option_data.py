from unittest.mock import Mock, patch

from quantresearch.data.options import (
    get_option_expirations,
)

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)

import pandas as pd
import pytest

from unittest.mock import Mock, patch

from quantresearch.data.models import (
    OptionChain,
    OptionQuote,
)

from quantresearch.instruments.options import (
    OptionContract,
    OptionType,
)


def test_get_option_expirations_returns_available_dates():

    mock_ticker = Mock()

    mock_ticker.options = (
        "2026-09-18",
        "2026-12-18",
        "2027-01-15",
    )

    with patch(
        "quantresearch.data.options.yf.Ticker",
        return_value=mock_ticker,
    ):

        expirations = get_option_expirations(
            "SPY"
        )

    assert expirations == [
        "2026-09-18",
        "2026-12-18",
        "2027-01-15",
    ]

from unittest.mock import Mock, patch

from quantresearch.data.options import (
    get_option_chain,
)


def test_get_option_chain_returns_chain():

    mock_chain = Mock()

    mock_ticker = Mock()
    mock_ticker.option_chain.return_value = mock_chain

    with patch(
        "quantresearch.data.options.yf.Ticker",
        return_value=mock_ticker,
    ):

        result = get_option_chain(
            symbol="SPY",
            expiration="2027-12-17",
        )

    mock_ticker.option_chain.assert_called_once_with(
        "2027-12-17"
    )

    assert result is mock_chain


import pandas as pd
import pytest

from quantresearch.data.options import (
    normalize_option_quote,
)


def test_normalize_option_quote():

    row = pd.Series(
        {
            "contractSymbol": "SPY271217C00500000",
            "lastTradeDate": pd.Timestamp(
                "2026-08-10 15:30:00"
            ),
            "strike": 500.0,
            "lastPrice": 72.50,
            "bid": 72.00,
            "ask": 73.00,
            "volume": 150,
            "openInterest": 2500,
            "impliedVolatility": 0.2145,
            "inTheMoney": True,
        }
    )

    quote = normalize_option_quote(row)

    assert quote.contract.underlying == "SPY"

    assert quote.contract.expiration == pd.Timestamp(
        "2027-12-17"
    )

    assert quote.contract.option_type == OptionType.CALL

    assert quote.contract.strike == pytest.approx(
        500.0
    )
    assert quote.last_trade_date == pd.Timestamp(
        "2026-08-10 15:30:00"
    )
    assert quote.contract.strike == pytest.approx(500.0)
    assert quote.last_price == pytest.approx(72.50)
    assert quote.bid == pytest.approx(72.00)
    assert quote.ask == pytest.approx(73.00)
    assert quote.volume == 150
    assert quote.open_interest == 2500
    assert quote.implied_volatility == pytest.approx(
        0.2145
    )
    assert quote.in_the_money is True

def test_normalize_option_quote_handles_missing_volume_and_open_interest():

    row = pd.Series(
        {
            "contractSymbol": "SPY271217C00500000",
            "lastTradeDate": pd.Timestamp(
                "2026-08-10 15:30:00"
            ),
            "strike": 500.0,
            "lastPrice": 72.50,
            "bid": 72.00,
            "ask": 73.00,
            "volume": float("nan"),
            "openInterest": float("nan"),
            "impliedVolatility": 0.2145,
            "inTheMoney": True,
        }
    )

    quote = normalize_option_quote(row)

    assert quote.volume is None
    assert quote.open_interest is None

from quantresearch.data.options import (
    normalize_option_quote,
    normalize_option_quotes,
)

def test_normalize_option_quotes_returns_list_of_quotes():

    dataframe = pd.DataFrame(
        [
            {
                "contractSymbol": "SPY271217C00500000",
                "lastTradeDate": pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                "strike": 500.0,
                "lastPrice": 72.50,
                "bid": 72.00,
                "ask": 73.00,
                "volume": 150,
                "openInterest": 2500,
                "impliedVolatility": 0.2145,
                "inTheMoney": True,
            },
            {
                "contractSymbol": "SPY271217C00550000",
                "lastTradeDate": pd.Timestamp(
                    "2026-08-10 15:31:00"
                ),
                "strike": 550.0,
                "lastPrice": 45.00,
                "bid": 44.50,
                "ask": 45.50,
                "volume": 75,
                "openInterest": 1800,
                "impliedVolatility": 0.2050,
                "inTheMoney": False,
            },
        ]
    )

    quotes = normalize_option_quotes(
        dataframe
    )

    assert len(quotes) == 2

    assert (
        quotes[0].contract.underlying
        == "SPY"
    )

    assert (
        quotes[0].contract.option_type
        == OptionType.CALL
    )

    assert quotes[0].contract.strike == pytest.approx(
        500.0
    )

    assert quotes[1].contract.strike == pytest.approx(
        550.0
    )

from unittest.mock import Mock

from quantresearch.data.models import (
    OptionChain,
    OptionQuote,
)
from quantresearch.data.options import (
    normalize_option_chain,
)

def test_normalize_option_chain_returns_calls_and_puts():

    calls = pd.DataFrame(
        [
            {
                "contractSymbol": "SPY271217C00500000",
                "lastTradeDate": pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                "strike": 500.0,
                "lastPrice": 72.50,
                "bid": 72.00,
                "ask": 73.00,
                "volume": 150,
                "openInterest": 2500,
                "impliedVolatility": 0.2145,
                "inTheMoney": True,
            },
        ]
    )

    puts = pd.DataFrame(
        [
            {
                "contractSymbol": "SPY271217P00500000",
                "lastTradeDate": pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                "strike": 500.0,
                "lastPrice": 18.50,
                "bid": 18.00,
                "ask": 19.00,
                "volume": 90,
                "openInterest": 1700,
                "impliedVolatility": 0.2250,
                "inTheMoney": False,
            },
        ]
    )

    yahoo_chain = Mock()
    yahoo_chain.calls = calls
    yahoo_chain.puts = puts

    chain = normalize_option_chain(
        yahoo_chain
    )

    assert isinstance(
        chain,
        OptionChain,
    )

    assert len(chain.calls) == 1
    assert len(chain.puts) == 1

    assert (
        chain.calls[0].contract.option_type
        == OptionType.CALL
    )

    assert chain.calls[0].contract.strike == pytest.approx(
        500.0
    )

    assert (
        chain.puts[0].contract.option_type
        == OptionType.PUT
    )

    assert chain.puts[0].contract.strike == pytest.approx(
        500.0
    )

from quantresearch.data.options import (
    download_option_chain,
)


def test_download_option_chain_returns_normalized_chain():

    yahoo_chain = Mock()

    yahoo_chain.calls = pd.DataFrame(
        [
            {
                "contractSymbol": "SPY271217C00500000",
                "lastTradeDate": pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                "strike": 500.0,
                "lastPrice": 72.50,
                "bid": 72.00,
                "ask": 73.00,
                "volume": 150,
                "openInterest": 2500,
                "impliedVolatility": 0.2145,
                "inTheMoney": True,
            },
        ]
    )

    yahoo_chain.puts = pd.DataFrame(
        [
            {
                "contractSymbol": "SPY271217P00500000",
                "lastTradeDate": pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                "strike": 500.0,
                "lastPrice": 18.50,
                "bid": 18.00,
                "ask": 19.00,
                "volume": 90,
                "openInterest": 1700,
                "impliedVolatility": 0.2250,
                "inTheMoney": False,
            },
        ]
    )

    with patch(
        "quantresearch.data.options.get_option_chain",
        return_value=yahoo_chain,
    ) as mock_get_option_chain:

        chain = download_option_chain(
            symbol="SPY",
            expiration="2027-12-17",
        )

    mock_get_option_chain.assert_called_once_with(
        symbol="SPY",
        expiration="2027-12-17",
    )

    assert isinstance(
        chain,
        OptionChain,
    )

    assert len(chain.calls) == 1
    assert len(chain.puts) == 1

    assert (
        chain.calls[0].contract.option_type
        == OptionType.CALL
    )

    assert chain.calls[0].contract.strike == pytest.approx(
        500.0
    )

import pytest

from quantresearch.data.options import (
    select_nearest_strike_call,
    
)

def test_select_nearest_strike_call():

    chain = OptionChain(
        calls=[
            OptionQuote(
                contract=OptionContract(
                    underlying="SPY",
                    expiration=pd.Timestamp(
                        "2027-12-17"
                    ),
                    strike=500.0,
                    option_type=OptionType.CALL,
                ),
                last_trade_date=pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                last_price=72.0,
                bid=71.5,
                ask=72.5,
                volume=200.0,
                open_interest=2000.0,
                implied_volatility=0.20,
                in_the_money=True,
            ),
            OptionQuote(
                contract=OptionContract(
                    underlying="SPY",
                    expiration=pd.Timestamp(
                        "2027-12-17"
                    ),
                    strike=500.0,
                    option_type=OptionType.CALL,
                ),
                last_trade_date=pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                last_price=72.0,
                bid=71.5,
                ask=72.5,
                volume=200.0,
                open_interest=2000.0,
                implied_volatility=0.20,
                in_the_money=True,
            ),
            OptionQuote(
                contract=OptionContract(
                    underlying="SPY",
                    expiration=pd.Timestamp(
                        "2027-12-17"
                    ),
                    strike=510.0,
                    option_type=OptionType.CALL,
                ),
                last_trade_date=pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),

                last_price=65.0,
                bid=64.5,
                ask=65.5,
                volume=150.0,
                open_interest=1500.0,
                implied_volatility=0.205,
                in_the_money=False,
            ),
        ],
        puts=[],
    )

    quote = select_nearest_strike_call(
        chain=chain,
        target_strike=503.0,
    )

    assert quote.contract.strike == pytest.approx(500.0)

    assert quote.contract.underlying == "SPY"

    assert quote.contract.expiration == pd.Timestamp(
        "2027-12-17"
    )

    assert quote.contract.option_type == OptionType.CALL

    assert quote.contract.strike == pytest.approx(
        500.0
    )

def test_select_nearest_strike_call_raises_when_no_calls():

    chain = OptionChain(
        calls=[],
        puts=[],
    )

    with pytest.raises(
        ValueError,
        match="no call contracts",
    ):
        select_nearest_strike_call(
            chain=chain,
            target_strike=500.0,
        )

from quantresearch.data.options import (
    select_atm_call,
)


def test_select_atm_call_returns_nearest_strike():

    chain = OptionChain(
        calls=[
            OptionQuote(
                contract=OptionContract(
                    underlying="SPY",
                    expiration=pd.Timestamp(
                        "2027-12-17"
                    ),
                    strike=500.0,
                    option_type=OptionType.CALL,
                ),
                last_trade_date=pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                last_price=72.0,
                bid=71.5,
                ask=72.5,
                volume=200.0,
                open_interest=2000.0,
                implied_volatility=0.20,
                in_the_money=True,
            ),
            OptionQuote(
                contract=OptionContract(
                    underlying="SPY",
                    expiration=pd.Timestamp(
                        "2027-12-17"
                    ),
                    strike=505.0,
                    option_type=OptionType.CALL,
                ),
                last_trade_date=pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                last_price=68.0,
                bid=67.5,
                ask=68.5,
                volume=180.0,
                open_interest=1900.0,
                implied_volatility=0.202,
                in_the_money=False,
            ),
        ],
        puts=[],
    )

    quote = select_atm_call(
        chain=chain,
        spot_price=503.0,
    )

    assert quote.contract.strike == pytest.approx(
        505.0
    )

from quantresearch.data.options import (
    select_expiration_by_dte,
)

def test_select_expiration_by_dte_returns_nearest_date():

    expirations = [
        "2027-06-18",
        "2027-09-17",
        "2027-12-17",
    ]

    reference_date = pd.Timestamp(
        "2026-08-10"
    )

    expiration = select_expiration_by_dte(
        expirations=expirations,
        reference_date=reference_date,
        target_dte=365,
    )

    assert expiration == "2027-09-17"

def test_select_expiration_by_dte_raises_when_no_expirations():

    with pytest.raises(
        ValueError,
        match="No option expirations available",
    ):
        select_expiration_by_dte(
            expirations=[],
            reference_date=pd.Timestamp(
                "2026-08-10"
            ),
            target_dte=365,
        )

from quantresearch.data.options import (
    select_expiration_in_dte_range,
)


def test_select_expiration_in_dte_range():

    expirations = [
        "2027-06-18",
        "2027-09-17",
        "2027-12-17",
        "2028-03-17",
    ]

    reference_date = pd.Timestamp(
        "2026-08-10"
    )

    expiration = (
        select_expiration_in_dte_range(
            expirations=expirations,
            reference_date=reference_date,
            min_dte=365,
            max_dte=550,
        )
    )

    assert expiration == "2027-12-17"

from quantresearch.data.options import (
    download_leaps_atm_call,
)

def test_download_leaps_atm_call():

    expirations = [
        "2027-06-18",
        "2027-09-17",
        "2027-12-17",
        "2028-03-17",
    ]

    chain = OptionChain(
        calls=[
            OptionQuote(
                contract=OptionContract(
                    underlying="SPY",
                    expiration=pd.Timestamp(
                        "2027-12-17"
                    ),
                    strike=500.0,
                    option_type=OptionType.CALL,
                ),
                last_trade_date=pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                last_price=72.0,
                bid=71.5,
                ask=72.5,
                volume=200.0,
                open_interest=2000.0,
                implied_volatility=0.20,
                in_the_money=True,
            ),
            OptionQuote(
                contract=OptionContract(
                    underlying="SPY",
                    expiration=pd.Timestamp(
                        "2027-12-17"
                    ),
                    strike=500.0,
                    option_type=OptionType.CALL,
                ),
                last_trade_date=pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                last_price=72.0,
                bid=71.5,
                ask=72.5,
                volume=200.0,
                open_interest=2000.0,
                implied_volatility=0.20,
                in_the_money=True,
            ),
            OptionQuote(
                contract=OptionContract(
                    underlying="SPY",
                    expiration=pd.Timestamp(
                        "2027-12-17"
                    ),
                    strike=500.0,
                    option_type=OptionType.CALL,
                ),
                last_trade_date=pd.Timestamp(
                    "2026-08-10 15:30:00"
                ),
                last_price=72.0,
                bid=71.5,
                ask=72.5,
                volume=200.0,
                open_interest=2000.0,
                implied_volatility=0.20,
                in_the_money=True,
            ),
        ],
        puts=[],
    )

    with patch(
        "quantresearch.data.options.get_option_expirations",
        return_value=expirations,
    ) as mock_expirations:

        with patch(
            "quantresearch.data.options.download_option_chain",
            return_value=chain,
        ) as mock_chain:

            quote = download_leaps_atm_call(
                symbol="SPY",
                spot_price=502.0,
                reference_date=pd.Timestamp(
                    "2026-08-10"
                ),
                min_dte=365,
                max_dte=550,
            )

    assert quote.contract.strike == pytest.approx(
        500.0
    )

    assert quote.contract.underlying == "SPY"

    assert quote.contract.expiration == pd.Timestamp(
        "2027-12-17"
    )

    assert quote.contract.option_type == OptionType.CALL

    assert quote.contract.strike == pytest.approx(
        500.0
    )

    mock_expirations.assert_called_once_with(
        "SPY"
    )

    mock_chain.assert_called_once_with(
        symbol="SPY",
        expiration="2027-12-17",
    )


def test_normalize_option_quote_parses_contract():

    row = pd.Series(
        {
            "contractSymbol": "SPY271217C00500000",
            "lastTradeDate": pd.Timestamp(
                "2026-08-10 15:30:00"
            ),
            "strike": 500.0,
            "lastPrice": 72.50,
            "bid": 72.00,
            "ask": 73.00,
            "volume": 150,
            "openInterest": 2500,
            "impliedVolatility": 0.2145,
            "inTheMoney": True,
        }
    )

    quote = normalize_option_quote(row)

    assert quote.contract.underlying == "SPY"

    assert quote.contract.expiration == pd.Timestamp(
        "2027-12-17"
    )

    assert quote.contract.option_type == OptionType.CALL

    assert quote.contract.strike == pytest.approx(
        500.0
    )

def test_normalize_option_quote_rejects_inconsistent_strike():

    row = pd.Series(
        {
            "contractSymbol": "SPY271217C00500000",
            "lastTradeDate": pd.Timestamp(
                "2026-08-10 15:30:00"
            ),
            "strike": 505.0,
            "lastPrice": 72.50,
            "bid": 72.00,
            "ask": 73.00,
            "volume": 150,
            "openInterest": 2500,
            "impliedVolatility": 0.2145,
            "inTheMoney": True,
        }
    )

    with pytest.raises(
        ValueError,
        match="strike does not match",
    ):
        normalize_option_quote(row)