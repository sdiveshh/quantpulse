import logging
import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from db import get_conn, get_qdrant  # noqa: E402

from fastembed import TextEmbedding  # noqa: E402
from qdrant_client.models import (  # noqa: E402
    Distance,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # noqa: E402

COLLECTION = "market_news"
MODEL = "BAAI/bge-small-en-v1.5"
DIM = 384
BATCH = 64

log = logging.getLogger("vector_indexer")


def ensure_collection(client):
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
        )
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name="ticker_tags",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        log.info("Created collection %s", COLLECTION)


def fetch_pending(conn, limit=500):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, ticker, source, headline, description, url, published_at
            FROM news_articles
            WHERE embedded_at IS NULL
            ORDER BY published_at DESC NULLS LAST
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def run():
    conn = get_conn()
    client = get_qdrant()
    try:
        ensure_collection(client)
        model = TextEmbedding(model_name=MODEL)
        sia = SentimentIntensityAnalyzer()
        total = 0
        while True:
            rows = fetch_pending(conn)
            if not rows:
                break
            for i in range(0, len(rows), BATCH):
                chunk = rows[i:i + BATCH]
                texts = [f"{r[3]}. {r[4] or ''}".strip() for r in chunk]
                vectors = list(model.embed(texts))
                points = []
                for r, text, vec in zip(chunk, texts, vectors):
                    points.append(PointStruct(
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{r[1]}|{r[5]}")),
                        vector=vec.tolist(),
                        payload={
                            "ticker_tags": [r[1]],
                            "source": r[2],
                            "headline": r[3],
                            "summary_chunk": r[4],
                            "url": r[5],
                            "published_at": r[6].isoformat() if r[6] else None,
                            "sentiment_score": sia.polarity_scores(text)["compound"],
                        },
                    ))
                client.upsert(collection_name=COLLECTION, points=points)
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE news_articles SET embedded_at = now() WHERE id = ANY(%s)",
                        ([r[0] for r in chunk],),
                    )
                conn.commit()
                total += len(chunk)
                log.info("Embedded %d articles so far", total)
        log.info("Done. %d new articles embedded", total)
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()