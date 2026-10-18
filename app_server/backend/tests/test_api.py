from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_tickers_list():
    r = client.get("/api/tickers")
    assert r.status_code == 200
    assert set(r.json()) == {"AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"}


def test_unknown_ticker_returns_404():
    assert client.get("/api/prices/XYZ").status_code == 404


def test_limit_must_be_positive():
    assert client.get("/api/prices/AAPL?limit=0").status_code == 422


def test_chat_rejects_short_question():
    assert client.post("/api/chat", json={"question": "hi"}).status_code == 422


def test_chat_rejects_missing_question():
    assert client.post("/api/chat", json={}).status_code == 422