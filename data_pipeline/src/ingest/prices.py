import logging

import yfinance as yf
from psycopg2.extras import execute_values

log = logging.getLogger(__name__)


def fetch_prices(ticker, period="5d", interval="15m"):
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        log.warning("No price data for %s", ticker)
        return []
    df = df.dropna(subset=["Close"])
    rows = []
    for ts, r in df.iterrows():
        rows.append((
            ticker,
            float(r["Open"]),
            float(r["High"]),
            float(r["Low"]),
            float(r["Close"]),
            int(r["Volume"]),
            ts.to_pydatetime(),
        ))
    return rows


def save_prices(conn, rows):
    if not rows:
        return 0
    sql = """
        INSERT INTO stock_prices
            (ticker, price_open, price_high, price_low, price_close, volume, timestamp)
        VALUES %s
        ON CONFLICT (ticker, timestamp) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)
        inserted = cur.rowcount
    conn.commit()
    return inserted