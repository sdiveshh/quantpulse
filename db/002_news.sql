CREATE TABLE IF NOT EXISTS news_articles (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    source VARCHAR(255),
    headline TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker, url)
);

CREATE INDEX IF NOT EXISTS idx_news_ticker_time ON news_articles (ticker, published_at DESC);