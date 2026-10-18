import logging
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from schemas import (
    Candle,
    ChatRequest,
    ChatResponse,
    Feature,
    NewsItem,
    PriceSeries,
    Summary,
)

log = logging.getLogger("backend")
TICKERS = {"AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"}

PRICES_SQL = """
SELECT timestamp, open, high, low, close, volume FROM (
    SELECT timestamp, price_open AS open, price_high AS high, price_low AS low,
           price_close AS close, volume
    FROM stock_prices WHERE ticker = $1
    ORDER BY timestamp DESC LIMIT $2
) t ORDER BY timestamp
"""

FEATURES_SQL = """
SELECT timestamp, close, return_pct, sma_20, volatility_20 FROM (
    SELECT timestamp, price_close AS close, return_pct, sma_20, volatility_20
    FROM stock_features WHERE ticker = $1
    ORDER BY timestamp DESC LIMIT $2
) t ORDER BY timestamp
"""

NEWS_SQL = """
SELECT ticker, source, headline, description, url, published_at
FROM news_articles
WHERE ($1::text IS NULL OR ticker = $1)
ORDER BY published_at DESC NULLS LAST
LIMIT $2
"""

SUMMARY_SQL = """
WITH daily AS (
    SELECT ticker, date_trunc('day', timestamp) AS d,
           (array_agg(price_close ORDER BY timestamp DESC))[1] AS close,
           max(timestamp) AS last_ts
    FROM stock_prices GROUP BY ticker, date_trunc('day', timestamp)
), ranked AS (
    SELECT ticker, close, last_ts,
           LAG(close) OVER (PARTITION BY ticker ORDER BY d) AS prev_close,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY d DESC) AS rn
    FROM daily
)
SELECT ticker, close AS last_price, prev_close, last_ts AS as_of,
       CASE WHEN prev_close > 0 THEN round(((close / prev_close) - 1) * 100, 3) END AS change_pct
FROM ranked WHERE rn = 1 ORDER BY ticker
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        host=settings.pg_host,
        port=settings.pg_port,
        user=settings.pg_user,
        password=settings.pg_password,
        database=settings.pg_db,
        min_size=1,
        max_size=5,
    )
    app.state.http = httpx.AsyncClient(timeout=90)
    yield
    await app.state.http.aclose()
    await app.state.pool.close()


app = FastAPI(title="QuantPulse API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def valid_ticker(ticker: str) -> str:
    t = ticker.upper()
    if t not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Unknown ticker {ticker}")
    return t


@app.get("/health")
async def health():
    try:
        await app.state.pool.fetchval("SELECT 1")
    except Exception:
        log.exception("DB health check failed")
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok", "db": True}


@app.get("/api/tickers", response_model=list[str])
async def tickers():
    return sorted(TICKERS)


@app.get("/api/summary", response_model=list[Summary])
async def summary():
    rows = await app.state.pool.fetch(SUMMARY_SQL)
    return [Summary(**dict(r)) for r in rows]


@app.get("/api/prices/{ticker}", response_model=PriceSeries)
async def prices(ticker: str, limit: int = Query(130, ge=1, le=1000)):
    t = valid_ticker(ticker)
    rows = await app.state.pool.fetch(PRICES_SQL, t, limit)
    return PriceSeries(ticker=t, candles=[Candle(**dict(r)) for r in rows])


@app.get("/api/features/{ticker}", response_model=list[Feature])
async def features(ticker: str, limit: int = Query(130, ge=1, le=1000)):
    t = valid_ticker(ticker)
    rows = await app.state.pool.fetch(FEATURES_SQL, t, limit)
    return [Feature(**dict(r)) for r in rows]


@app.get("/api/news", response_model=list[NewsItem])
async def news(ticker: Optional[str] = None, limit: int = Query(20, ge=1, le=100)):
    t = valid_ticker(ticker) if ticker else None
    rows = await app.state.pool.fetch(NEWS_SQL, t, limit)
    return [NewsItem(**dict(r)) for r in rows]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        resp = await app.state.http.post(f"{settings.ai_url}/chat", json=req.model_dump())
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="AI service is not reachable")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="AI service could not answer right now")
    return ChatResponse(**resp.json())