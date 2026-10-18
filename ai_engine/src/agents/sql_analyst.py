import json
import re

from pydantic import BaseModel

from agents.llm import get_llm
from db import get_conn

ALLOWED_TABLES = {"stock_prices", "stock_features"}
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|call|do|execute|vacuum|set)\b|pg_",
    re.I,
)

SCHEMA = """PostgreSQL tables:
stock_prices(ticker, price_open, price_high, price_low, price_close, volume, timestamp)
  -- 15-minute bars. timestamp is timestamptz (UTC).
stock_features(ticker, timestamp, price_close, return_pct, sma_20, volatility_20)
  -- derived per 15-minute bar. return_pct is percent change vs previous bar.
Tickers: AAPL, MSFT, GOOGL, TSLA, NVDA"""

RULES = """Write ONE PostgreSQL SELECT query. Rules:
- Use only the tables and columns above.
- Only SELECT (a WITH clause is allowed). No semicolons.
- Always end with LIMIT 100 or less.
- For daily figures group by date_trunc('day', timestamp). Never use EXTRACT(... FROM ...).
- Ticker values are uppercase string literals.
- Interpret "latest", "today", "recent" relative to the data range given, not the current date.
- To compare volatility across tickers use stddev(return_pct) from stock_features. Do not compare volatility_20 across tickers, because it is in dollars and depends on the price level.
- For "most", "least", "highest" or "best" across tickers, return one row per ticker ordered by the metric (do not use LIMIT 1), so the full ranking is visible."""


class SQLQuery(BaseModel):
    sql: str


def validate_sql(sql: str) -> str:
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        raise ValueError("Only one statement is allowed")
    if not re.match(r"^(select|with)\b", s, re.I):
        raise ValueError("Query must start with SELECT or WITH")
    if FORBIDDEN.search(s):
        raise ValueError("Query contains a forbidden keyword")
    ctes = {m.lower() for m in re.findall(r"\b(\w+)\s+as\s*\(", s, re.I)}
    tables = {t.lower() for t in re.findall(r"\b(?:from|join)\s+([\w\.]+)", s, re.I)}
    bad = {t for t in tables if t not in ALLOWED_TABLES and t not in ctes}
    if bad:
        raise ValueError(f"Tables not allowed: {sorted(bad)}")
    if not re.search(r"\blimit\b", s, re.I):
        s += " LIMIT 100"
    return s


def run_query(sql: str):
    conn = get_conn()
    try:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 5000")
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchmany(100)
        return cols, rows
    finally:
        conn.close()


def data_range() -> str:
    _, rows = run_query("SELECT min(timestamp), max(timestamp) FROM stock_prices")
    return f"{rows[0][0]} to {rows[0][1]} (UTC)"


def answer_sql(question: str, tickers: list) -> dict:
    llm = get_llm().with_structured_output(SQLQuery)
    rng = data_range()
    feedback = ""
    last_error = ""
    for _ in range(3):
        prompt = (
            f"{SCHEMA}\n\nData covers: {rng}\n\n{RULES}\n\n"
            f"Question: {question}\nTickers of interest: {tickers or 'any'}\n{feedback}"
        )
        out = llm.invoke([("system", "You are an expert PostgreSQL analyst."), ("human", prompt)])
        try:
            sql = validate_sql(out.sql)
            cols, rows = run_query(sql)
            data = [dict(zip(cols, r)) for r in rows]
            return {"sql": sql, "sql_result": json.dumps(data, default=str)[:6000]}
        except Exception as e:
            last_error = str(e)
            feedback = f"\nYour previous query failed:\n{out.sql}\nError: {last_error}\nFix it."
    return {"sql": None, "sql_result": f"Could not produce a valid query: {last_error}"}