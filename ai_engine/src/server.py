import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from agents.graph import build_graph  # noqa: E402

log = logging.getLogger("ai_service")
state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["graph"] = build_graph()
    yield


app = FastAPI(title="QuantPulse AI engine", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        out = state["graph"].invoke({"question": req.question})
    except Exception:
        log.exception("Agent failed")
        raise HTTPException(
            status_code=503,
            detail="The AI service could not answer right now. Try again in a minute.",
        )
    return {
        "route": out.get("route"),
        "tickers": out.get("tickers", []),
        "sql": out.get("sql"),
        "answer": out["answer"],
    }