from quantresearch.data.models import (
    OptionChain,
    OptionQuote,
)

from quantresearch.instruments.options import (
    parse_option_contract_symbol,
)

import pandas as pd
import yfinance as yf


def get_option_expirations(
    symbol: str,
) -> list[str]:

    ticker = yf.Ticker(symbol)

    return list(ticker.options)

def get_option_chain(
    symbol: str,
    expiration: str,
):
    ticker = yf.Ticker(symbol)

    return ticker.option_chain(
        expiration
    )

def normalize_option_quote(
    row: pd.Series,
) -> OptionQuote:

    contract = parse_option_contract_symbol(
        row["contractSymbol"]
    )

    row_strike = float(
        row["strike"]
    )

    if row_strike != contract.strike:
        raise ValueError(
            "Option quote strike does not match "
            "contract symbol strike."
        )

    return OptionQuote(
        contract=contract,
        last_trade_date=row["lastTradeDate"],
        last_price=float(row["lastPrice"]),
        bid=float(row["bid"]),
        ask=float(row["ask"]),
        volume=(
            None
            if pd.isna(row["volume"])
            else float(row["volume"])
        ),
        open_interest=(
            None
            if pd.isna(row["openInterest"])
            else float(
                row["openInterest"]
            )
        ),
        implied_volatility=float(
            row["impliedVolatility"]
        ),
        in_the_money=bool(
            row["inTheMoney"]
        ),
    )

def normalize_option_quotes(
    dataframe: pd.DataFrame,
) -> list[OptionQuote]:

    return [
        normalize_option_quote(row)
        for _, row in dataframe.iterrows()
    ]

from quantresearch.data.models import (
    OptionChain,
    OptionQuote,
)

def normalize_option_chain(
    chain,
) -> OptionChain:

    return OptionChain(
        calls=normalize_option_quotes(
            chain.calls
        ),
        puts=normalize_option_quotes(
            chain.puts
        ),
    )

def download_option_chain(
    symbol: str,
    expiration: str,
) -> OptionChain:

    chain = get_option_chain(
        symbol=symbol,
        expiration=expiration,
    )

    return normalize_option_chain(
        chain
    )

def select_nearest_strike_call(
    chain: OptionChain,
    target_strike: float,
) -> OptionQuote:

    if not chain.calls:
        raise ValueError(
            "Option chain contains no call contracts."
        )

    return min(
        chain.calls,
        key=lambda quote: abs(
            quote.contract.strike
            - target_strike
        ),
    )

def select_atm_call(
    chain: OptionChain,
    spot_price: float,
) -> OptionQuote:

    return select_nearest_strike_call(
        chain=chain,
        target_strike=spot_price,
    )

def select_expiration_by_dte(
    expirations: list[str],
    reference_date: pd.Timestamp,
    target_dte: int,
) -> str:

    if not expirations:
        raise ValueError(
            "No option expirations available."
        )

    return min(
        expirations,
        key=lambda expiration: abs(
            (
                pd.Timestamp(expiration)
                - reference_date
            ).days
            - target_dte
        ),
    )


def select_expiration_in_dte_range(
    expirations: list[str],
    reference_date: pd.Timestamp,
    min_dte: int,
    max_dte: int,
) -> str:

    eligible = [
        expiration
        for expiration in expirations
        if min_dte
        <= (
            pd.Timestamp(expiration)
            - reference_date
        ).days
        <= max_dte
    ]

    if not eligible:
        raise ValueError(
            "No option expiration found "
            "within the requested DTE range."
        )

    target_dte = (
        min_dte + max_dte
    ) / 2

    return min(
        eligible,
        key=lambda expiration: abs(
            (
                pd.Timestamp(expiration)
                - reference_date
            ).days
            - target_dte
        ),
    )

def download_leaps_atm_call(
    symbol: str,
    spot_price: float,
    reference_date: pd.Timestamp,
    min_dte: int = 365,
    max_dte: int = 550,
) -> OptionQuote:

    expirations = get_option_expirations(
        symbol
    )

    expiration = (
        select_expiration_in_dte_range(
            expirations=expirations,
            reference_date=reference_date,
            min_dte=min_dte,
            max_dte=max_dte,
        )
    )

    chain = download_option_chain(
        symbol=symbol,
        expiration=expiration,
    )

    return select_atm_call(
        chain=chain,
        spot_price=spot_price,
    )