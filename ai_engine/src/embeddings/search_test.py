import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from db import get_qdrant  # noqa: E402

from fastembed import TextEmbedding  # noqa: E402
from qdrant_client.models import FieldCondition, Filter, MatchValue  # noqa: E402

from vector_indexer import COLLECTION, MODEL  # noqa: E402

query = sys.argv[1] if len(sys.argv) > 1 else "chip demand"
ticker = sys.argv[2] if len(sys.argv) > 2 else None

vec = list(TextEmbedding(model_name=MODEL).embed([query]))[0].tolist()
flt = None
if ticker:
    flt = Filter(must=[FieldCondition(key="ticker_tags", match=MatchValue(value=ticker))])

res = get_qdrant().query_points(
    collection_name=COLLECTION, query=vec, limit=5, query_filter=flt, with_payload=True
)
for p in res.points:
    pl = p.payload
    print(f"{p.score:.3f} | {pl['ticker_tags'][0]} | sent {pl['sentiment_score']:+.2f} | {pl['headline']}")