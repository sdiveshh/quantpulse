from typing import Literal

from pydantic import BaseModel, Field

from agents.llm import get_llm

TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

SYSTEM = """You route questions for a stock market assistant.
Pick one route:
- "sql": needs numbers from market data (prices, highs/lows, volume, returns, moving averages, volatility, comparisons).
- "research": needs news, sentiment, or qualitative context (why something is moving, what is being reported).
- "both": needs numbers AND news context.
Also list the tickers the question is about, using only these: AAPL, MSFT, GOOGL, TSLA, NVDA
(Apple=AAPL, Microsoft=MSFT, Google/Alphabet=GOOGL, Tesla=TSLA, Nvidia=NVDA). Return an empty list if none are mentioned or the question covers all of them."""


class Route(BaseModel):
    route: Literal["sql", "research", "both"] = Field(description="Which agent path to use")
    tickers: list[str] = Field(description="Tickers mentioned, may be empty")


def classify(question: str) -> Route:
    llm = get_llm().with_structured_output(Route)
    out = llm.invoke([("system", SYSTEM), ("human", question)])
    out.tickers = [t.upper() for t in out.tickers if t.upper() in TICKERS]
    return out