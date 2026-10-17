CREATE TABLE IF NOT EXISTS stock_features (
    ticker VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    price_close NUMERIC(12,4),
    return_pct NUMERIC(10,6),
    sma_20 NUMERIC(12,4),
    volatility_20 NUMERIC(10,6),
    PRIMARY KEY (ticker, timestamp)
);