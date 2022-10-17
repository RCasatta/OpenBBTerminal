"""Yahoo Finance model"""
__docformat__ = "numpy"

import os
import sys
import logging
from typing import Dict, List

import yfinance as yf
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime

from openbb_terminal.decorators import log_start_end

logger = logging.getLogger(__name__)

FUTURES_DATA = pd.read_csv(os.path.join("openbb_terminal", "futures", "futures.csv"))

MONTHS = {
    1: "F",
    2: "G",
    3: "H",
    4: "J",
    5: "K",
    6: "M",
    7: "N",
    8: "Q",
    9: "U",
    10: "V",
    11: "X",
    12: "Z",
}


class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


@log_start_end(log=logger)
def get_search_futures(
    category: str = "",
    exchange: str = "",
):
    """Get search futures [Source: Yahoo Finance]

    Parameters
    ----------
    category: str
        Select the category where the future exists
    exchange: str
        Select the exchange where the future exists
    """
    if category and exchange:
        df = FUTURES_DATA[
            (FUTURES_DATA["Exchange"] == exchange)
            & (FUTURES_DATA["Category"] == category)
        ]
    elif category:
        df = FUTURES_DATA[FUTURES_DATA["Category"] == category]
    elif exchange:
        df = FUTURES_DATA[FUTURES_DATA["Exchange"] == exchange]
    else:
        df = FUTURES_DATA
    return df


@log_start_end(log=logger)
def get_historical_futures(tickers: List[str]) -> Dict:
    """Get historical futures [Source: Yahoo Finance]

    Parameters
    ----------
    tickers: List[str]
        List of future timeseries tickers to display

    Returns
    ----------
    Dict
        Dictionary with sector weightings allocation
    """
    df = yf.download(tickers, progress=False, period="max")
    return df


@log_start_end(log=logger)
def get_curve_futures(
    ticker: str = "",
):
    """Get curve futures [Source: Yahoo Finance]

    Parameters
    ----------
    ticker: str
        Ticker to get forward curve
    """
    if ticker not in FUTURES_DATA["Ticker"].unique().tolist():
        return pd.DataFrame()

    exchange = FUTURES_DATA[FUTURES_DATA["Ticker"] == ticker]["Exchange"].values[0]
    today = datetime.today()

    futures_index = list()
    futures_curve = list()
    for i in range(36):
        future = today + relativedelta(months=i)
        future_ticker = (
            f"{ticker}{MONTHS[future.month]}{str(future.year)[-2:]}.{exchange}"
        )

        with HiddenPrints():
            data = yf.download(future_ticker, progress=False)

        if not data.empty:
            futures_index.append(future.strftime("%Y-%b"))
            futures_curve.append(data["Adj Close"].values[-1])

    if not futures_index:
        return pd.DataFrame()

    return pd.DataFrame(index=futures_index, data=futures_curve, columns=["Futures"])
