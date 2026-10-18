import logging

from db import get_conn
from news import fetch_news, save_news
from prices import fetch_prices, save_prices

TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stream_processor")


def run(do_prices=True, do_news=True):
    conn = get_conn()
    price_failures = 0
    news_failures = 0
    try:
        for t in TICKERS:
            if do_prices:
                try:
                    n = save_prices(conn, fetch_prices(t))
                    log.info("%s: %d new price rows", t, n)
                except Exception:
                    conn.rollback()
                    price_failures += 1
                    log.exception("Price ingest failed for %s", t)
            if do_news:
                try:
                    n = save_news(conn, fetch_news(t))
                    log.info("%s: %d new news rows", t, n)
                except Exception:
                    conn.rollback()
                    news_failures += 1
                    log.exception("News ingest failed for %s", t)
    finally:
        conn.close()
    if do_prices and price_failures == len(TICKERS):
        raise RuntimeError("Price ingest failed for every ticker")
    if do_news and news_failures == len(TICKERS):
        raise RuntimeError("News ingest failed for every ticker")


if __name__ == "__main__":
    run()