import logging

from db import get_conn
from news import fetch_news, save_news
from prices import fetch_prices, save_prices

TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stream_processor")


def run():
    conn = get_conn()
    price_failures = 0
    try:
        for t in TICKERS:
            try:
                n = save_prices(conn, fetch_prices(t))
                log.info("%s: %d new price rows", t, n)
            except Exception:
                conn.rollback()
                price_failures += 1
                log.exception("Price ingest failed for %s", t)
            try:
                n = save_news(conn, fetch_news(t))
                log.info("%s: %d new news rows", t, n)
            except Exception:
                conn.rollback()
                log.exception("News ingest failed for %s", t)
    finally:
        conn.close()
    if price_failures == len(TICKERS):
        raise RuntimeError("Price ingest failed for every ticker")


if __name__ == "__main__":
    run()