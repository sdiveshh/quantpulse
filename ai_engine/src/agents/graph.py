import json
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.llm import get_llm
from agents.research_agent import research
from agents.router import classify
from agents.sql_analyst import answer_sql


class State(TypedDict, total=False):
    question: str
    route: str
    tickers: list
    sql: Optional[str]
    sql_result: str
    news_context: str
    answer: str


def router_node(state: State):
    r = classify(state["question"])
    return {"route": r.route, "tickers": r.tickers}


def sql_node(state: State):
    return answer_sql(state["question"], state.get("tickers", []))


def research_node(state: State):
    tickers = state.get("tickers", [])
    if not tickers and state.get("sql_result"):
        try:
            rows = json.loads(state["sql_result"])
            tickers = list(dict.fromkeys(r["ticker"] for r in rows if "ticker" in r))[:2]
        except Exception:
            tickers = []
    return {"news_context": research(state["question"], tickers)}


def synthesize_node(state: State):
    parts = []
    if state.get("sql_result"):
        parts.append(f"MARKET DATA (SQL result):\n{state['sql_result']}")
    if state.get("news_context"):
        parts.append(f"NEWS CONTEXT:\n{state['news_context']}")
    prompt = (
        "You are QuantPulse, a concise financial markets assistant. Answer the question using ONLY "
        "the data below. Quote concrete numbers and name headlines with their source when you use news. "
        "The price data is 15-minute bars from the most recent trading days, not live. If the data does "
        "not answer the question, say so. This is information, not financial advice.\n\n"
        + "\n\n".join(parts)
        + f"\n\nQuestion: {state['question']}"
    )
    content = get_llm().invoke(prompt).content
    if isinstance(content, list):
        content = "".join(p if isinstance(p, str) else p.get("text", "") for p in content)
    return {"answer": content}


def after_router(state: State):
    return "sql_analyst" if state["route"] in ("sql", "both") else "research_agent"


def after_sql(state: State):
    return "research_agent" if state["route"] == "both" else "synthesize"


def build_graph():
    g = StateGraph(State)
    g.add_node("router", router_node)
    g.add_node("sql_analyst", sql_node)
    g.add_node("research_agent", research_node)
    g.add_node("synthesize", synthesize_node)
    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router", after_router, {"sql_analyst": "sql_analyst", "research_agent": "research_agent"}
    )
    g.add_conditional_edges(
        "sql_analyst", after_sql, {"research_agent": "research_agent", "synthesize": "synthesize"}
    )
    g.add_edge("research_agent", "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()