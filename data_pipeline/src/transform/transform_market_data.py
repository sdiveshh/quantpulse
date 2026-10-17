import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "ingest"))
from db import get_conn  # noqa: E402

log = logging.getLogger("transform")

CHECKS = {
    "null_or_nonpositive_close": "SELECT count(*) FROM stock_prices WHERE price_close IS NULL OR price_close <= 0",
    "high_below_low": "SELECT count(*) FROM stock_prices WHERE price_high < price_low",
    "negative_volume": "SELECT count(*) FROM stock_prices WHERE volume < 0",
}

FEATURES_SQL = """
INSERT INTO stock_features (ticker, timestamp, price_close, return_pct, sma_20, volatility_20)
SELECT
    ticker,
    timestamp,
    price_close,
    (price_close / NULLIF(LAG(price_close) OVER w, 0) - 1) * 100,
    AVG(price_close) OVER (w ROWS BETWEEN 19 PRECEDING AND CURRENT ROW),
    STDDEV(price_close) OVER (w ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
FROM stock_prices
WINDOW w AS (PARTITION BY ticker ORDER BY timestamp)
ON CONFLICT (ticker, timestamp) DO UPDATE SET
    price_close = EXCLUDED.price_close,
    return_pct = EXCLUDED.return_pct,
    sma_20 = EXCLUDED.sma_20,
    volatility_20 = EXCLUDED.volatility_20
"""


def validate(conn):
    bad = {}
    with conn.cursor() as cur:
        for name, sql in CHECKS.items():
            cur.execute(sql)
            n = cur.fetchone()[0]
            if n:
                bad[name] = n
    if bad:
        raise ValueError(f"Data quality checks failed: {bad}")
    log.info("All data quality checks passed")


def run():
    conn = get_conn()
    try:
        validate(conn)
        with conn.cursor() as cur:
            cur.execute(FEATURES_SQL)
            log.info("Upserted %d feature rows", cur.rowcount)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()