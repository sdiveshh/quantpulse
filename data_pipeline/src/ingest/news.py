import logging
import os

import requests
from psycopg2.extras import execute_values

log = logging.getLogger(__name__)

NEWS_URL = "https://newsapi.org/v2/everything"
COMPANY = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
}


def fetch_news(ticker, page_size=20):
    key = os.getenv("NEWS_API_KEY")
    if not key or key.startswith("your_"):
        log.warning("NEWS_API_KEY not set, skipping news for %s", ticker)
        return []
    query = f'"{COMPANY.get(ticker, ticker)}" AND (stock OR shares OR earnings)'
    resp = requests.get(
        NEWS_URL,
        params={
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
        },
        headers={"X-Api-Key": key},
        timeout=20,
    )
    resp.raise_for_status()
    rows = []
    for a in resp.json().get("articles", []):
        if not a.get("url") or not a.get("title"):
            continue
        rows.append((
            ticker,
            (a.get("source") or {}).get("name"),
            a["title"],
            a.get("description"),
            a["url"],
            a.get("publishedAt"),
        ))
    return rows


def save_news(conn, rows):
    if not rows:
        return 0
    sql = """
        INSERT INTO news_articles
            (ticker, source, headline, description, url, published_at)
        VALUES %s
        ON CONFLICT (ticker, url) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=500)
        inserted = cur.rowcount
    conn.commit()
    return inserted