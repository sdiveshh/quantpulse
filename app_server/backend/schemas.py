from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceSeries(BaseModel):
    ticker: str
    interval: str = "15m"
    candles: list[Candle]


class Feature(BaseModel):
    timestamp: datetime
    close: Optional[float] = None
    return_pct: Optional[float] = None
    sma_20: Optional[float] = None
    volatility_20: Optional[float] = None


class NewsItem(BaseModel):
    ticker: str
    source: Optional[str] = None
    headline: str
    description: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None


class Summary(BaseModel):
    ticker: str
    last_price: float
    prev_close: Optional[float] = None
    change_pct: Optional[float] = None
    as_of: datetime


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class ChatResponse(BaseModel):
    route: Optional[str] = None
    tickers: list[str] = []
    sql: Optional[str] = None
    answer: str