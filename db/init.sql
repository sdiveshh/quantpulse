CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    portfolio_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE stock_prices (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price_open NUMERIC(12,4),
    price_high NUMERIC(12,4),
    price_low NUMERIC(12,4),
    price_close NUMERIC(12,4),
    volume BIGINT,
    timestamp TIMESTAMPTZ NOT NULL,
    UNIQUE (ticker, timestamp)
);

CREATE INDEX idx_ticker_time ON stock_prices (ticker, timestamp DESC);