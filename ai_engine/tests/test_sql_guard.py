import pytest

from agents.sql_analyst import validate_sql


def test_accepts_simple_select_and_adds_limit():
    sql = validate_sql("SELECT max(price_high) FROM stock_prices WHERE ticker = 'AAPL'")
    assert sql.upper().endswith("LIMIT 100")


def test_keeps_existing_limit():
    sql = "SELECT * FROM stock_prices LIMIT 5"
    assert validate_sql(sql) == sql


def test_allows_cte():
    sql = (
        "WITH t AS (SELECT ticker, stddev(return_pct) AS v FROM stock_features GROUP BY ticker) "
        "SELECT * FROM t ORDER BY v DESC"
    )
    assert validate_sql(sql).startswith("WITH")


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE stock_prices",
        "DELETE FROM stock_prices",
        "SELECT 1; DROP TABLE stock_prices",
        "UPDATE stock_prices SET volume = 0",
        "INSERT INTO stock_prices VALUES (1)",
        "SELECT * FROM portfolios",
        "SELECT * FROM news_articles",
        "SELECT pg_sleep(10)",
    ],
)
def test_rejects_unsafe_sql(sql):
    with pytest.raises(ValueError):
        validate_sql(sql)