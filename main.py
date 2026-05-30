#!/usr/bin/env python3
"""
Stock market data pipeline CLI.

Usage:
    fetch  <TICKER> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--interval 1d]
    query  <TICKER> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--limit N]
    quote  <TICKER>
    list
"""

import argparse
import sys
from datetime import date, timedelta

from pipeline import fetch as fetcher, store


def cmd_fetch(args):
    provider = fetcher.DEFAULT_PROVIDER
    start = date.fromisoformat(args.start) if args.start else date.today() - timedelta(days=365)
    end = date.fromisoformat(args.end) if args.end else date.today()

    print(f"Fetching {args.ticker.upper()} {start} → {end} [{args.interval}] …")
    df = provider.fetch_history(args.ticker, start, end, args.interval)

    conn = store.get_conn()
    n = store.upsert(conn, args.ticker, df)
    conn.close()
    print(f"Stored {n} rows for {args.ticker.upper()}.")


def cmd_query(args):
    conn = store.get_conn()
    df = store.query(
        conn,
        args.ticker,
        start=args.start,
        end=args.end,
        limit=args.limit,
    )
    conn.close()
    if df.empty:
        print(f"No data for {args.ticker.upper()}. Run: python main.py fetch {args.ticker}")
        sys.exit(1)
    print(df.to_string())


def cmd_quote(args):
    provider = fetcher.DEFAULT_PROVIDER
    q = provider.fetch_quote(args.ticker)
    print(f"{q['ticker']}  price={q['price']:.2f}  prev_close={q['previous_close']:.2f}  as_of={q['timestamp']} UTC")


def cmd_list(args):
    conn = store.get_conn()
    rows = store.list_tickers(conn)
    conn.close()
    if not rows:
        print("No data stored yet. Run: python main.py fetch <TICKER>")
        return
    print(f"{'TICKER':<10} {'ROWS':>6}  {'FIRST':<12} {'LAST':<12}")
    print("-" * 44)
    for ticker, count, first, last in rows:
        print(f"{ticker:<10} {count:>6}  {first:<12} {last:<12}")


def main():
    parser = argparse.ArgumentParser(description="Stock market data pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="Fetch and store historical OHLCV data")
    p_fetch.add_argument("ticker")
    p_fetch.add_argument("--start", help="YYYY-MM-DD (default: 1 year ago)")
    p_fetch.add_argument("--end", help="YYYY-MM-DD (default: today)")
    p_fetch.add_argument("--interval", default="1d",
                         help="1m/5m/1h/1d/1wk/1mo (default: 1d)")
    p_fetch.set_defaults(func=cmd_fetch)

    p_query = sub.add_parser("query", help="Query stored price data")
    p_query.add_argument("ticker")
    p_query.add_argument("--start")
    p_query.add_argument("--end")
    p_query.add_argument("--limit", type=int, default=30)
    p_query.set_defaults(func=cmd_query)

    p_quote = sub.add_parser("quote", help="Fetch latest quote (not stored)")
    p_quote.add_argument("ticker")
    p_quote.set_defaults(func=cmd_quote)

    p_list = sub.add_parser("list", help="List stored tickers")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
