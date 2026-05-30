# Bassem Platform

Monorepo for the Bassem platform. Contains a Next.js web app, stock market data pipeline, and shared infrastructure.

---

## Project Structure

```
.
├── app/                    # Next.js 16 web application (React 19, TypeScript, Tailwind 4)
├── pipeline/               # Python stock market data pipeline
│   ├── __init__.py
│   ├── fetch.py            # DataProvider ABC + YFinanceProvider
│   └── store.py            # SQLite upsert + query helpers
├── scripts/                # Infrastructure and setup scripts
│   └── setup-github-org.sh # GitHub org/repo/branch protection setup
├── data/                   # Data storage (SQLite, auto-created)
├── .github/                # GitHub configuration
│   ├── workflows/
│   │   ├── ci.yml          # CI pipeline (lint, typecheck, test)
│   │   └── deploy.yml      # CD pipeline (build, deploy on main)
│   ├── ISSUE_TEMPLATE/     # Bug report and feature request templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── dependabot.yml
├── main.py                 # Python CLI entry point
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Web App (Next.js)

The `app/` directory contains a Next.js 16 application with React 19, TypeScript, and Tailwind CSS 4.

```bash
cd app
npm ci
npm run dev        # Development server (port 3000)
npm run build      # Production build
npm run lint       # ESLint
npm run typecheck  # TypeScript type checking
```

---

## Stock Market Data Pipeline (Python)

Minimal spike: fetch price data for any ticker, store in SQLite, query via CLI.
Spike goal: validate feasibility and data source options before a full build.

---

## Quick Start

```bash
# Create venv and install deps
uv venv .venv
uv pip install -r requirements.txt --python .venv/bin/python

# Fetch 1 year of daily OHLCV for AAPL
python main.py fetch AAPL

# Query last 10 rows
python main.py query AAPL --limit 10

# Latest real-time quote
python main.py quote AAPL

# List all stored tickers
python main.py list
```

---

## Commands

| Command | What it does |
|---------|-------------|
| `fetch <TICKER>` | Download historical OHLCV, upsert into SQLite |
| `query <TICKER>` | Read stored rows, print as table |
| `quote <TICKER>` | Fetch live price (not stored) |
| `list` | Show all stored tickers + row counts + date range |

### fetch options

```
python main.py fetch AAPL --start 2024-01-01 --end 2024-12-31 --interval 1d
```

`--interval` values: `1m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1wk`, `1mo`
Note: intraday intervals (< 1d) limited to 60 days of history by Yahoo Finance.

---

## Data Sources

### Current: yfinance (Yahoo Finance) — free, no API key

| Property | Detail |
|----------|--------|
| Cost | Free |
| API key | None required |
| Historical depth | Daily: back to IPO; intraday: 60 days |
| Rate limit | ~2000 req/hour per IP (unofficial) |
| Delay | 15 min delayed for real-time; historical is complete |
| Data quality | Good for equities, ETFs, indices, crypto |
| Intervals | 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo |

### Evaluated Alternatives

| Provider | Free Tier | Paid From | Notes |
|----------|-----------|-----------|-------|
| **Alpha Vantage** | 25 req/day | $50/mo | REST API, API key required, good fundamentals |
| **Polygon.io** | 15-min delayed, unlimited | $29/mo | Best API design; WebSocket for real-time |
| **Twelve Data** | 800 req/day, 8/min | $29/mo | WebSocket supported; good for intraday |
| **Finnhub** | 60 req/min | $50/mo | Real-time WebSocket, strong alternative data |
| **NASDAQ Data Link** | Public datasets free | varies | Best for fundamentals + macro data |
| **IEX Cloud** | 500K msg/mo | $19/mo | Solid data quality, US equities focus |

**Recommendation for production:**
- **Stay on yfinance** if bulk daily historical + delayed quotes suffice (zero cost).
- **Upgrade to Polygon.io** if you need real-time WebSocket data or options chains.
- **Add Alpha Vantage** if you need earnings, balance sheets, or macro indicators.

---

## Storage

SQLite at `data/prices.db`. Schema:

```sql
CREATE TABLE prices (
    ticker  TEXT NOT NULL,
    date    TEXT NOT NULL,   -- ISO 8601: YYYY-MM-DD
    open    REAL,
    high    REAL,
    low     REAL,
    close   REAL,
    volume  INTEGER,
    PRIMARY KEY (ticker, date)  -- upsert-safe
);
```

WAL mode enabled for concurrent readers. Primary key on `(ticker, date)` means repeated fetches are idempotent.

---

## Fetch Frequency

| Use case | Recommended interval | Feasibility |
|----------|---------------------|-------------|
| EOD swing analysis | Daily, after 4pm ET | ✅ yfinance, free |
| Intraday signals | 5m/15m, max 60-day lookback | ✅ yfinance, free |
| Real-time alerts | WebSocket tick | ⚠️ Needs Polygon or Finnhub paid |
| Options chains | On-demand | ⚠️ yfinance partial; Polygon paid |

---

## How to Extend

### Swap the data provider

`pipeline/fetch.py` has an abstract `DataProvider` base. Add a new class:

```python
class PolygonProvider(DataProvider):
    def __init__(self, api_key: str):
        self.client = RESTClient(api_key)

    def fetch_history(self, ticker, start, end, interval="1d") -> pd.DataFrame:
        # ... map Polygon aggs → OHLCV DataFrame
        pass

    def fetch_quote(self, ticker) -> dict:
        # ... latest trade
        pass
```

Then in `fetch.py` set `DEFAULT_PROVIDER = PolygonProvider(os.environ["POLYGON_KEY"])`.

### Add a scheduler

For automated fetching, add a cron/systemd timer that runs:

```bash
python main.py fetch AAPL
python main.py fetch MSFT
```

Or use APScheduler inside the app for in-process scheduling.

### Add more indicators

`pipeline/store.py` returns a pandas DataFrame — plug in `pandas-ta` or `ta-lib` downstream:

```python
import pandas_ta as ta
df = store.query(conn, "AAPL", limit=200)
df["rsi"] = ta.rsi(df["close"], length=14)
```

### Upgrade storage for scale

SQLite handles millions of rows fine for a single server. When multi-server or streaming ingest is needed, swap `store.py` for TimescaleDB (Postgres + time-series extension) — the DataFrame interface stays identical.

---

## CI/CD Pipeline

### CI (`.github/workflows/ci.yml`)
Triggers on push to `main`/`develop` and PRs to `main`.
- Installs Node.js 20.x dependencies in `app/`
- Runs lint, typecheck, and tests
- Skips gracefully if no test script is configured

### CD (`.github/workflows/deploy.yml`)
Triggers on push to `main`.
- Builds the Next.js app for production
- Runs smoke tests
- Deployment targets (Vercel, Railway, SSH) can be uncommented when ready

### Branch Protection
Run `scripts/setup-github-org.sh` with `GH_TOKEN`, `ORG_NAME`, `REPO_NAME` to auto-configure:
- Required status checks (`test`)
- 1 approving review required
- Dismiss stale reviews on new pushes

---

## Smoke Test Results (2026-05-30)

```
$ python main.py fetch AAPL --start 2025-01-01
Stored 101 rows for AAPL.

$ python main.py fetch MSFT --start 2025-01-01
Stored 352 rows for MSFT.

$ python main.py query AAPL --limit 3
                  open        high         low       close    volume
date
2025-05-29  202.775558  203.004645  197.725585  199.159897  51396800
2025-05-28  199.797363  201.928906  199.110087  199.628036  45339700
2025-05-27  197.516413  199.946773  196.649840  199.418869  56288500

$ python main.py quote AAPL
AAPL  price=312.06  prev_close=311.84  as_of=2026-05-30T00:59:38 UTC

$ python main.py list
TICKER       ROWS  FIRST        LAST
--------------------------------------------
AAPL          101  2025-01-02   2025-05-29
MSFT          352  2025-01-02   2026-05-29
```
