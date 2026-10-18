from functools import lru_cache

from fastembed import TextEmbedding
from qdrant_client.models import FieldCondition, Filter, MatchAny

from db import get_qdrant
from embeddings.vector_indexer import COLLECTION, MODEL


@lru_cache(maxsize=1)
def _embedder():
    return TextEmbedding(model_name=MODEL)


def research(question: str, tickers: list, limit: int = 6) -> str:
    vec = list(_embedder().embed([question]))[0].tolist()
    flt = None
    if tickers:
        flt = Filter(must=[FieldCondition(key="ticker_tags", match=MatchAny(any=tickers))])
    res = get_qdrant().query_points(
        collection_name=COLLECTION,
        query=vec,
        limit=limit * 2,
        query_filter=flt,
        with_payload=True,
    )
    seen, lines = set(), []
    for p in res.points:
        pl = p.payload
        if pl["headline"] in seen:
            continue
        seen.add(pl["headline"])
        date = (pl.get("published_at") or "")[:10]
        lines.append(
            f"[{pl['ticker_tags'][0]} | {pl.get('source')} | {date} | sentiment {pl['sentiment_score']:+.2f}] "
            f"{pl['headline']} - {pl.get('summary_chunk') or ''}"
        )
        if len(lines) >= limit:
            break
    return "\n".join(lines) if lines else "No relevant news found."