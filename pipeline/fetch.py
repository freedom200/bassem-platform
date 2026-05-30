"""Data provider abstraction + yfinance implementation."""

from __future__ import annotations

import abc
from datetime import date, datetime
from typing import Optional

import pandas as pd
import yfinance as yf


class DataProvider(abc.ABC):
    """Swap implementations to change data source without touching the rest of the pipeline."""

    @abc.abstractmethod
    def fetch_history(
        self,
        ticker: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Return OHLCV DataFrame indexed by date."""

    @abc.abstractmethod
    def fetch_quote(self, ticker: str) -> dict:
        """Return latest quote as a dict with at least {price, timestamp}."""


class YFinanceProvider(DataProvider):
    """
    Free, no API key. Data sourced from Yahoo Finance.
    Rate limit: ~2000 req/hour per IP (unofficial).
    Intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    Intraday history available up to 60 days back; daily goes to IPO date.
    """

    def fetch_history(
        self,
        ticker: str,
        start: date,
        end: Optional[date] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        t = yf.Ticker(ticker)
        df = t.history(
            start=start.isoformat(),
            end=end.isoformat() if end else None,
            interval=interval,
            auto_adjust=True,
        )
        if df.empty:
            raise ValueError(f"No data returned for {ticker} ({start} → {end})")
        df.index = df.index.tz_localize(None)  # strip tz for SQLite compat
        df.index.name = "date"
        return df[["Open", "High", "Low", "Close", "Volume"]]

    def fetch_quote(self, ticker: str) -> dict:
        t = yf.Ticker(ticker)
        info = t.fast_info
        return {
            "ticker": ticker.upper(),
            "price": info.last_price,
            "previous_close": info.previous_close,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Default provider — swap to AlphaVantageProvider, PolygonProvider, etc. here
DEFAULT_PROVIDER = YFinanceProvider()
